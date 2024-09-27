import csv
import os
import re
import json
from openai import OpenAI

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAIKEY')
client = OpenAI(api_key=openai_api_key)

def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def extract_table_of_contents(text):
    start_index = text.find("Sisukord")
    if start_index == -1:
        return None
    end_index = text.find("\n\n", start_index)
    toc = text[start_index:end_index].strip() if end_index != -1 else text[start_index:].strip()
    return toc

def format_using_gpt(toc, bird_name):
    # Provide a detailed prompt with example JSON to guide the GPT model
    prompt = (
        f"Kasutades järgnevat sisukorda:\n\n{toc}\n\n"
        "Palun lahenda selle põhjal ja tagasta JSON formaadis, "
        f"mis osad on seotud {bird_name} linnuga ja järgmiste teemadega:\n"
        "'Elupaik', 'Elupaiga seisund', 'Ohud', "
        "'Populatsiooni muutused Eestis', 'Uuringud', 'Seisund ELis', 'Kokkuvõte'.\n\n"
        "Struktuur peaks olla nagu nii:\n"
        "```json\n"
        "{\n"
        f"   \"Lind\": [\n"
        "      {\n"
        "         \"Elupaik\": [\"8.2.1.1 Elupaiganõudlus\"]\n"
        "      },\n"
        "      {\n"
        "         \"Elupaiga seisund\": [\"8.2.1.1 Elupaiganõudlus\"]\n"
        "      },\n"
        "      {\n"
        "         \"Ohud\": [\"8.2.3 Kaitsestaatus ja senise kaitse tõhususe analüüs\"]\n"
        "      },\n"
        "      {\n"
        "         \"Populatsiooni muutused Eestis\": [\"8.2.2.2 Levik ja arvukus Eestis\"]\n"
        "      },\n"
        "      {\n"
        "         \"Uuringud\": [\n"
        "            \"8.2.2.1 Levik ja arvukus maailmas ja Euroopas\",\n"
        "            \"8.2.2.2 Levik ja arvukus Eestis\",\n"
        "            \"8.2.3 Kaitsestaatus ja senise kaitse tõhususe analüüs\"\n"
        "         ]\n"
        "      },\n"
        "      {\n"
        "         \"Seisund ELis\": [\"8.2.2.1 Levik ja arvukus maailmas ja Euroopas\"]\n"
        "      },\n"
        "      {\n"
        "         \"Kokkuvõte\": [\"Kokkuvõte\"]\n"
        "      }\n"
        "   ]\n"
        "}\n"
        "```\n"
    )

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "Oled abivalmis assistent, kes aitab teksti analüüsida ja struktuurida."},
            {"role": "user", "content": prompt}
        ]
    )

    json_response = response.choices[0].message.content
    print(json_response)
    return preprocess_json_response(json_response)

def preprocess_json_response(json_response):
    try:
        response_json = json.loads(json_response)
        return transform_json_response(response_json)
    except json.JSONDecodeError:
        match = re.search(r'```json\n([\s\S]*?)\n```', json_response)
        if match:
            json_text = match.group(1)
            try:
                response_json = json.loads(json_text)
                return transform_json_response(response_json)
            except json.JSONDecodeError:
                print("Error parsing JSON from extracted block: ", json_text)
                return None
        else:
            print("Error: No JSON found in response. Got: ", json_response)
            return None

def transform_json_response(response_json):
    if not isinstance(response_json, dict):
        print("Expected response_json to be a dictionary")
        return None

    bird_name = list(response_json.keys())[0]
    sections = response_json[bird_name]
    transformed_data = {}

    for section in sections:
        for key, values in section.items():
            transformed_data[key] = ", ".join(values)

    return transformed_data

def save_to_csv(data, output_file="output.csv"):
    if not data:
        return
    fieldnames = data[0].keys()
    with open(output_file, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for entry in data:
            writer.writerow(entry)

def main():
    os.chdir('/home/teks/PycharmProjects/biodiversity')
    input_csv = 'failed.csv'
    results = []

    with open(input_csv, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            strategy_file = row['strategy_file']
            bird_name = row['Estonian Name']
            bird_id = bird_name[:-3]

            text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '_cleaned.txt'))
            text = read_text_from_file(text_file_path)
            toc = extract_table_of_contents(text)

            if toc:
                if (bird_id.lower() in strategy_file.lower() or (bird_id.lower() in toc.lower())):
                    json_results = format_using_gpt(toc, bird_name)
                    if json_results:
                        row.update(json_results)
                        results.append(row)

    save_to_csv(results)

if __name__ == '__main__':
    main()
