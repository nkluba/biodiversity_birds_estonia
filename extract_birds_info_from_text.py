import json
import re
import os
import pandas as pd
from openai import OpenAI

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAIKEY')
client = OpenAI(api_key=openai_api_key)

# Function to read text from a file
def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def transform_json_response(response_json):
    # Ensure values are all strings and lists are joined into a single string
    for key, value in response_json.items():
        if isinstance(value, list):
            # Join list items with commas
            response_json[key] = ', '.join(value)
        elif not isinstance(value, str):
            # Convert any non-string values (unexpected) to a string
            response_json[key] = str(value)
    return response_json

# New function: format using GPT per section
def format_using_gpt_per_section(parameter, text):
    prompt = f"""
    Otsi järgnevas tekstis lindude jaoks infot teemal: {parameter}.
    Tagastage võimalikult üksikasjalikud andmed iga parameetri kohta ühtset teksti, kuid mitte rohkem kui 10 lauset. Tagasta kokkuvõte antud teemal või NA kui andmeid ei leidu. Ärge lisage ise mingit teksti.

    {text}
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Oled abivalmis assistent, kes aitab ekstraktitud teavet vormindada."},
            {"role": "user", "content": prompt}
        ]
    )

    section_response = response.choices[0].message.content
    print(section_response)
    return section_response.strip()

# Function to format information for full description using ChatGPT
def format_using_gpt(text):
    prompt = (
        f"Otsi järgnevas tekstis kirjed ja vorminda info JSON-struktuurina loendava nimekirjaga (Tagastage võimalikult üksikasjalikud andmed iga parameetri kohta ühtset teksti, kuid mitte rohkem kui 10 lauset):\n\n{text}\n\n"
        "Struktuur on järgmine (kui teave puudub tekstis, tagasta 'NA'):\n"
        "{\n"
        '  "Kirjeldus (seisund, elupaik, populatsiooni muutused)": "NA",\n'
        '  "Ohutegurite kirjeldus (ohud, elupaiga seisund)": "NA",\n'
        "}\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Oled abivalmis assistent, kes aitab ekstraktitud teavet vormindada."},
            {"role": "user", "content": prompt}
        ]
    )

    json_response = response.choices[0].message.content

    # Attempt to parse the response content directly as JSON
    try:
        response_json = json.loads(json_response)
        formatted_response = transform_json_response(response_json)
        return formatted_response
    except json.JSONDecodeError:
        match = re.search(r'```json\n([\s\S]*?)\n```', json_response)
        if match:
            json_text = match.group(1)
            try:
                response_json = json.loads(json_text)
                return response_json
            except json.JSONDecodeError:
                print("Error parsing JSON from extracted block: ", json_text)
                return None
        else:
            print("Error: No JSON found in response. Got: ", json_response)
            print(text)
            return None

    return None

def parse_json_to_dataframe_columns(json_data):
    if json_data:
        return {k: [v] for k, v in json_data.items()}
    else:
        return {}

# Main processing function
def main():
    # Load the CSV file
    df = pd.read_csv('st7_texts_prepared_for_analysis.csv').fillna('')[:3]

    formatted_responses = []
    response_dfs = []

    # Process each row in the DataFrame
    for index, row in df.iterrows():
        estonian_name = row['Estonian Name']
        print(estonian_name)

        if row['Analyze_by_sisukord'] == False:
            formatted_text = format_using_gpt(row['Kokkuvõte_text'])
            if formatted_text:
                formatted_responses.append(formatted_text)
                response_dfs.append(parse_json_to_dataframe_columns(formatted_text))
        else:
            # If Analyze_by_sisukord is True, process sections individually
            kirjeldus_texts = ' '.join(text for text in [row.get('Elupaik_text', ''), row.get('Populatsiooni muutused Eestis_text', ''), row.get('Seisund ELis_text', '')])
            ohud_texts = ' '.join(text for text in [row.get('Elupaiga seisund_text', ''), row.get('Ohud_text', '')])
            sections_dict = {
                'Kirjeldus (seisund, elupaik, populatsiooni muutused)': format_using_gpt_per_section(
                    'Kirjeldus (seisund, elupaik, populatsiooni muutused)',
                    kirjeldus_texts
                ),
                'Ohutegurite kirjeldus (ohud, elupaiga seisund)': format_using_gpt_per_section(
                    'Ohutegurite kirjeldus (ohud, elupaiga seisund)',
                    ohud_texts
                )
            }
            formatted_responses.append(sections_dict)
            response_dfs.append(parse_json_to_dataframe_columns(sections_dict))

    # You can now add response_dfs back to the original DataFrame or save it as needed
    for i, response_df in enumerate(response_dfs):
        for column, value in response_df.items():
            df.at[i, column] = value[0]

    df.to_csv('st8_birds_data_extracted.csv', index=False)

    # Save the version for display

    columns_to_keep = [
        'Estonian Name',
        'Latin Name',
        'Category',
        'EELIS link',
        'strategy_present',
        'Nimi inglise k',
        'Rühm',
        'Kaitsekategooria',
        'Kirjeldus (seisund, elupaik, populatsiooni muutused)',
        'Ohutegurite kirjeldus (ohud, elupaiga seisund)'
    ]

    df_selected = df[columns_to_keep]

    df_selected.to_csv('updated_birds_descriptions.csv', index=False)

if __name__ == "__main__":
    main()
