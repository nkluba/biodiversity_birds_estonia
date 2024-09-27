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


# Function to format extracted information using ChatGPT
def format_using_gpt(text):
    prompt = (
        f"Vorminda järgmine teave JSON-struktuurina selgel ja struktureeritud viisil:\n\n{text}\n\n"
        "Struktuur on järgmine (KUI TEAVE PUUDUB TEKSTIS, JÄÄTA 'NA'; kui on antud mitu vastust, "
        "liituge need üheks sõneks ja eraldage need komadega):\n"
        "{\n"
        '  "Elupaik": "NA",\n'
        '  "Elupaiga seisund": "NA",\n'
        '  "Ohud": "NA",\n'  # Here, list items will be joined by commas
        '  "Populatsiooni muutused Eestis": "NA",\n'  # Join the details by commas
        '  "Kas rändlinnud": "NA",\n'
        '  "Läbiviidud uuringud": "NA",\n'
        '  "Kavandatud uuringud": "NA",\n'
        '  "Seisund ELis": "NA",\n'
        '  "Populatsiooni muutused teistes ELi riikides": "NA"\n'  # Join by commas
        "}\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
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
        # If direct parsing fails, attempt to extract JSON within triple backticks using regex
        match = re.search(r'```json\n([\s\S]*?)\n```', json_response)
        if match:
            json_text = match.group(1)
            try:
                # Try parsing the extracted text as JSON
                response_json = json.loads(json_text)
                return response_json
            except json.JSONDecodeError:
                print("Error parsing JSON from extracted block: ", json_text)
                return None
        else:
            print("Error: No JSON found in response. Got: ", json_response)
            return None

    return None

def parse_json_to_dataframe_columns(json_data):
    if json_data:
        # For each key/value in the JSON response, return it mapped as a column
        return {k: [v] for k, v in json_data.items()}
    else:
        # If there's no JSON data, return an empty mapping
        return {}


def extract_kokkuvote_section(text):
    # Pattern to find Kokkuvõte section assuming it's a standalone section.
    kokkuvote_pattern = re.compile(r'Kokkuvõte(.*?)\n\s*\n', re.DOTALL)
    match = kokkuvote_pattern.search(text)
    if match:
        return match.group(1).strip()
    return None


# Main processing function
def main():
    # Load the CSV file
    df = pd.read_csv('st5_relevant_pdf_reports.csv').fillna('')

    formatted_responses = []
    response_dfs = []

    # Process each row in the DataFrame
    for index, row in df.iterrows():
        estonian_name = row['Estonian Name']
        kirjeldus_text = str(row.get('Kirjeldus'))
        ohutegurite_kirjeldus_text = str(row.get('Ohutegurite kirjeldus'))
        kirjeldus = kirjeldus_text + ' ' + ohutegurite_kirjeldus_text
        strategy_present = row.get('strategy_present', False)  # Assuming this is how strategy_present is stored

        concatenated_texts = []  # List to hold all formatted texts

        if not kirjeldus.isspace():
            # Format the combined 'Kirjeldus' and 'Ohutegurite kirjeldus'
            formatted_text = format_using_gpt(kirjeldus)
            if formatted_text:
                concatenated_texts.append(formatted_text)

        # Read from the text file converted from PDF
        strategy_file = row['strategy_file']
        text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '_cleaned.txt'))
        text = read_text_from_file(text_file_path)

        # Decide whether to extract Kokkuvõte section or use extract_bird_sections
        if strategy_present:
            kokkuvote_section = extract_kokkuvote_section(text)
            if kokkuvote_section:
                formatted_text = format_using_gpt(kokkuvote_section)
                if formatted_text:
                    concatenated_texts.append(formatted_text)
            else:
                # Fallback to extracting bird sections
                bird_sections = extract_bird_sections(text, estonian_name)
                extracted_text = "\n".join(bird_sections)

                if extracted_text:
                    # Format the extracted sections
                    formatted_text = format_using_gpt(extracted_text)
                    if formatted_text:
                        concatenated_texts.append(formatted_text)

        # Combine all JSON responses into one
        combined_json = {}
        for response_json in concatenated_texts:
            for key, value in response_json.items():
                if key in combined_json:
                    # If already present, make sure it is a string before concatenating
                    combined_json[key] = str(combined_json[key])
                    print(
                        f"Key: {key}, Value: {value}, Current combined_json[key]: {combined_json.get(key, 'Not set')}")
                    combined_json[key] += f" / {value}" if value != "NA" else ""
                else:
                    combined_json[key] = value

        # Convert JSON response into DataFrame-compatible format
        json_columns = parse_json_to_dataframe_columns(combined_json)
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


# - check if pdf is bird-centered or not; if is, then extract only Kokkuvotte part (if present)