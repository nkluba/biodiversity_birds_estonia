import os
import re
import json
import pandas as pd
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
    return text[start_index:end_index].strip() if end_index != -1 else text[start_index:].strip()

def format_using_gpt(toc, bird_name):
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
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Oled abivalmis assistent, kes aitab teksti analüüsida ja struktuurida."},
            {"role": "user", "content": prompt}
        ]
    )

    json_response = response.choices[0].message.content
    processed_json_response = preprocess_json_response(json_response)
    return transform_json_response(processed_json_response)

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
                return response_json
            except json.JSONDecodeError:
                print("Error parsing JSON from extracted block:", json_text)
                return None
        else:
            print("Error: No JSON found in response. Got:", json_response)
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

def main():
    os.chdir('/home/teks/PycharmProjects/biodiversity')
    input_csv = 'failed.csv'
    df = pd.read_csv(input_csv)

    results = []

    for index, row in df.iterrows():
        strategy_file = row['strategy_file']
        bird_name = row['Estonian Name']
        bird_id = bird_name[:-3]

        text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '_cleaned.txt'))
        text = read_text_from_file(text_file_path)
        toc = extract_table_of_contents(text)

        if toc:
            if bird_id.lower() in strategy_file.lower() or bird_id.lower() in toc.lower():
                json_results = format_using_gpt(toc, bird_name)
                if json_results:
                    for key, value in json_results.items():
                        row[key] = value
                    results.append(row)

    result_df = pd.DataFrame(results)
    result_df.to_csv("output.csv", index=False, encoding='utf-8')


#if __name__ == '__main__':
#    main()
