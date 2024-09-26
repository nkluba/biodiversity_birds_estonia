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

# Function to extract relevant sections using regex
def extract_bird_sections(text, bird_name):
    # Regex pattern to find blocks where bird_name is mentioned, capturing surrounding context
    bird_pattern = re.compile(
        rf'(^(?:(?!\n\s*\n).)*\b{bird_name}\b(?:(?!\n\s*\n).)*$)',
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    matches = bird_pattern.findall(text)

    # Clean up the extracted sections
    cleaned_matches = [re.sub(r'\s+', ' ', match).strip() for match in matches]
    return cleaned_matches

# Function to format extracted information using ChatGPT
def format_using_gpt(text):
    prompt = (
        f"Vorminda järgmine teave JSON-struktuurina selgel ja struktureeritud viisil:\n\n{text}\n\n"
        "Struktuur on järgmine (KUI TEAVE PUUDUB TEKSTIS, JÄÄTA 'NA'):\n"
        "{\n"
        '  "Elupaik": "NA",\n'
        '  "Elupaiga seisund": "NA",\n'
        '  "Ohud": "NA",\n'
        '  "Populatsiooni muutused": "NA",\n'
        '  "Kas rändlinnud": "NA",\n'
        '  "Läbiviidud uuringud": "NA",\n'
        '  "Kavandatud uuringud": "NA",\n'
        '  "Seisund ELis": "NA",\n'
        '  "Populatsioonitrend teistes ELi riikides": "NA"\n'
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
    match = re.search(r'```json\n([\s\S]*?)\n```', json_response)
    if match:
        json_text = match.group(1)
    else:
        print("Error: No JSON found in response. Got: ", json_response)
        return None

    try:
        response_json = json.loads(json_text)
    except json.JSONDecodeError:
        print("Error parsing JSON: ", json_text)
        return None

    return response_json

def parse_json_to_dataframe_columns(json_data):
    if json_data:
        # For each key/value in the JSON response, return it mapped as a column
        return {k: [v] for k, v in json_data.items()}
    else:
        # If there's no JSON data, return an empty mapping
        return {}


# Main processing function
def main():
    # Load the CSV file
    df = pd.read_csv('st5_relevant_pdf_reports.csv')[:2].fillna('')

    formatted_responses = []
    response_dfs = []

    # Process each row in the DataFrame
    for index, row in df.iterrows():
        estonian_name = row['Estonian Name']
        kirjeldus_text = str(row.get('Kirjeldus'))
        ohutegurite_kirjeldus_text = str(row.get('Ohutegurite kirjeldus'))
        kirjeldus = kirjeldus_text + ' ' + ohutegurite_kirjeldus_text

        strategy_file = row['strategy_file']
        if not kirjeldus.isspace():
            # Format the combined 'Kirjeldus' and 'Ohutegurite kirjeldus'
            formatted_text = format_using_gpt(kirjeldus)
        else:
            # Read from the text file converted from PDF
            text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '_cleaned.txt'))
            text = read_text_from_file(text_file_path)

            # Extract relevant sections for the bird
            bird_sections = extract_bird_sections(text, estonian_name)
            extracted_text = "\n".join(bird_sections)

            if extracted_text:
                # Format the extracted sections
                formatted_text = format_using_gpt(extracted_text)
            else:
                formatted_text = "No relevant sections found."

        # Convert JSON response into DataFrame-compatible format
        json_columns = parse_json_to_dataframe_columns(formatted_text)
        formatted_responses.append(json_columns)

        # Store the response DataFrame for later concatenation
        response_df = pd.DataFrame(json_columns, index=[index])
        response_dfs.append(response_df)

    if response_dfs:
        # Concatenate all response DataFrames before inserting them into the main DataFrame
        all_responses_df = pd.concat(response_dfs, axis=0)

        # Concatenate with the original DataFrame
        df = pd.concat([df, all_responses_df], axis=1)

        # Save the DataFrame to a new CSV file
    df.to_csv('st5_relevant_pdf_reports_with_responses.csv', index=False)

if __name__ == "__main__":
    main()


# - get response as JSON and set to columns
# - if one of kirjeldus/ohu_kirjendus is empty, construct query to get missing values from pdf's
# - if kirjeldus+ohu_kirjendus after first request go through columns and for NA submit new query basing on pdf
# - check if pdf is bird-centered or not; if is, then extract only Kokkuvotte part (if present)