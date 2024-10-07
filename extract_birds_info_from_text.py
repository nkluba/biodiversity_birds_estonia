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
    Otsi järgnevas tekstis linnu kohta käivad lühikesed kokkuvõtted teemal: {parameter}.
    Tagasta lühike kokkuvõte loendavas nimekirjas või NA kui andmeid ei leidu. Ärge lisage ise mingit teksti.

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
    return section_response.strip()

# Function to format information for full description using ChatGPT
def format_using_gpt(text):
    prompt = (
        f"Otsi järgnevas tekstis kirjed ja vorminda info JSON-struktuurina selgel ning lühendatud kujul loendava nimekirjaga:\n\n{text}\n\n"
        "Struktuur on järgmine (kui teave puudub tekstis, tagasta 'NA', kui esineb mitu vastet, liitu need komadega üheks sõneks):\n"
        "{\n"
        '  "Elupaik": "NA",\n'
        '  "Elupaiga seisund": "NA",\n'
        '  "Ohud": "NA",\n'
        '  "Populatsiooni muutused Eestis": "NA",\n'
        '  "Kas rändlinnud": "NA",\n'
        '  "Läbiviidud uuringud": "NA",\n'
        '  "Kavandatud uuringud": "NA",\n'
        '  "Seisund ELis": "NA",\n'
        '  "Populatsiooni muutused teistes ELi riikides": "NA"\n'
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
    df = pd.read_csv('st7_texts_prepared_for_analysis.csv').fillna('')

    formatted_responses = []
    response_dfs = []

    # Process each row in the DataFrame
    for index, row in df.iterrows():
        estonian_name = row['Estonian Name']
        kirjeldus_text = str(row.get('Kirjeldus'))
        ohutegurite_kirjeldus_text = str(row.get('Ohutegurite kirjeldus'))
        kirjeldus = kirjeldus_text + ' ' + ohutegurite_kirjeldus_text
        combined_text = ' '.join([row['Kokkuvõte_text'], kirjeldus])
        print(estonian_name)

        if row['Analyze_by_sisukord'] == False and not kirjeldus.isspace():
            # Step 1: If Analyze_by_sisukord is False, combine kirjeldus and Kokkuvõte_text
            formatted_text = format_using_gpt(combined_text)
            if formatted_text:
                formatted_responses.append(formatted_text)
                response_dfs.append(parse_json_to_dataframe_columns(formatted_text))
        elif not row['Analyze_by_sisukord'] and kirjeldus.isspace():
            formatted_text = format_using_gpt(row['Kokkuvõte_text'])
            if formatted_text:
                formatted_responses.append(formatted_text)
                response_dfs.append(parse_json_to_dataframe_columns(formatted_text))
        else:
            # Step 2: If Analyze_by_sisukord is True, process sections individually
            sections_dict = {
                'Elupaik': format_using_gpt_per_section('Elupaik', row.get('Elupaik_text', '') or kirjeldus),
                'Elupaiga seisund': format_using_gpt_per_section('Elupaiga seisund',
                                                                 row.get('Elupaiga seisund_text', '') or kirjeldus),
                'Ohud': format_using_gpt_per_section('Ohud', row.get('Ohud_text', '') or kirjeldus),
                'Populatsiooni muutused Eestis': format_using_gpt_per_section('Populatsiooni muutused Eestis',
                                                                              row.get('Populatsiooni muutused Eestis_text',
                                                                                      '') or kirjeldus),
                'Seisund ELis': format_using_gpt_per_section('Seisund ELis', row.get('Seisund ELis_text', '') or kirjeldus),
                'Kas rändlinnud': format_using_gpt_per_section('Kas rändlinnud', combined_text),
                'Läbiviidud uuringud': format_using_gpt_per_section('Läbiviidud uuringud', row.get('Uuringud_text', '')),
                'Kavandatud uuringud': format_using_gpt_per_section('Kavandatud uuringud', row.get('Uuringud_text', '')),
                'Populatsiooni muutused teistes ELi riikides': format_using_gpt_per_section(
                    'Populatsiooni muutused teistes ELi riikides', combined_text)
            }

            formatted_responses.append(sections_dict)
            response_dfs.append(parse_json_to_dataframe_columns(sections_dict))

    # You can now add response_dfs back to the original DataFrame or save it as needed
    for i, response_df in enumerate(response_dfs):
        for column, value in response_df.items():
            df.at[i, column] = value[0]

    df.to_csv('st8_birds_data_extracted.csv', index=False)

if __name__ == "__main__":
    main()
