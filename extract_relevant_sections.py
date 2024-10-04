import os
import re
import json
import pandas as pd
from openai import OpenAI
from extract_sections_texts import extract_full_table_of_contents

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAIKEY')
client = OpenAI(api_key=openai_api_key)

def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def extract_bird_related_text(text, bird_name):
    lines = text.split('\n')
    result = []
    capture_lines = 30  # Define the number of lines to capture before and after
    n = len(lines)

    for i in range(n):
        if bird_name in lines[i]:
            start = max(0, i - capture_lines)  # Ensure we don't go out of bounds at the start
            end = min(n, i + capture_lines + 1)  # Ensure we don't go out of bounds at the end
            result.extend(lines[start:end])
            i += capture_lines  # Move the index forward to continue from +20 line

    result = list(set(list(result)))
    return "\n".join(result)


def split_text_into_chunks(text, max_tokens):
    words = text.split()
    current_chunk = []
    current_chunk_tokens = 0

    chunks = []
    for word in words:
        word_tokens = len(word)  # Simplified token estimation
        if current_chunk_tokens + word_tokens > max_tokens:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_chunk_tokens = 0
        current_chunk.append(word)
        current_chunk_tokens += word_tokens

    if current_chunk:
        chunks.append(' '.join(current_chunk))

    return chunks


def extract_bird_sections(text, bird_name):
    # Extract relevant sections related to the bird
    text = extract_bird_related_text(text, bird_name[:-2])

    # Split the text into chunks suitable for the language model
    chunks_for_llm = split_text_into_chunks(text, 128000)

    # Initialize a variable to hold the concatenated responses
    combined_response = ""

    for chunk in chunks_for_llm:
        # Create the prompt for each chunk
        prompt = f"""
        Otsi järgnevas tekstis lõigud, mis on seotud linnuga '{bird_name}', ja kombineeri need.
        Tagasta tulemused ühe tekstina.

        {chunk}
        """

        # Call the OpenAI API with the constructed prompt
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Oled abivalmis assistent, kes aitab teksti analüüsida."},
                {"role": "user", "content": prompt}
            ]
        )

        # Append the response for each chunk to the combined response
        extracted_text = response.choices[0].message.content
        combined_response += extracted_text + "\n"

    return combined_response.strip()


def format_using_gpt(toc, bird_name, multiple_bird_centered):
    if multiple_bird_centered:
        prompt = (
            f"Kasutades järgnevat sisukorda:\n\n{toc}\n\n"
            "Palun lahenda selle põhjal ja tagasta JSON formaadis, "
            f"mis osad on seotud linnuga {bird_name} ja järgmiste teemadega:\n"
            "'Elupaik', 'Elupaiga seisund', 'Ohud', "
            "'Populatsiooni muutused Eestis', 'Uuringud', 'Seisund ELis', 'Kokkuvõte'."
            "\n\nArvesta, et kui on seotud mitme linnuliigiga käsitletud osad, "
            "siis need lisatakse vastavatesse kategooriatesse.\n"
            "Näiteks lindu 'Hallhani' analüüsides lisatakse ka '3. Ohutegurid'.\n\n"
            "Struktuur peaks olla järgmine:\n"
            "```json\n"
            "{\n"
            f"   \"{bird_name}\": [\n"
            "      {\n"
            "         \"Elupaik\": [\"2.2.1.1 Elupaiganõudlus\"]\n"
            "      },\n"
            "      {\n"
            "         \"Elupaiga seisund\": [\"2.2.1.1 Elupaiganõudlus\"]\n"
            "      },\n"
            "      {\n"
            "         \"Ohud\": [\"3. Ohutegurid\", \"2.2.4 Kaitsestaatus ja senise kaitse tõhususe analüüs\"]\n"
            "      },\n"
            "      {\n"
            "         \"Populatsiooni muutused Eestis\": [\"2.2.3.2 Levik ja arvukus Eestis\"]\n"
            "      },\n"
            "      {\n"
            "         \"Uuringud\": [\n"
            "            \"2.2.2 Ülevaade uuringutest ja inventuuridest\",\n"
            "            \"2.2.3.1 Levik ja arvukus Euroopas\",\n"
            "            \"2.2.3.2 Levik ja arvukus Eestis\"\n"
            "         ]\n"
            "      },\n"
            "      {\n"
            "         \"Seisund ELis\": [\"2.2.3.1 Levik ja arvukus Euroopas\"]\n"
            "      },\n"
            "      {\n"
            "         \"Kokkuvõte\": [\"Kokkuvõte\"]\n"
            "      }\n"
            "   ]\n"
            "}\n"
            "```\n"
        )
    else:
        prompt = (
            f"Kasutades järgnevat sisukorda:\n\n{toc}\n\n"
            "Palun lahenda selle põhjal ja tagasta JSON formaadis, "
            f"mis osad on seotud järgmiste teemadega:\n"
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
    input_csv = 'sample.csv'
    df = pd.read_csv(input_csv)

    results = []

    for index, row in df.iterrows():
        strategy_file = row['strategy_file']
        bird_name = row['Estonian Name']
        bird_id = bird_name[:-2]

        text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '_cleaned.txt'))
        text = read_text_from_file(text_file_path)
        toc, toc_start, toc_end = extract_full_table_of_contents(text)

        if toc:
            one_bird_centered = False
            multiple_bird_centered = False

            if bird_id.lower() in toc.lower():
                multiple_bird_centered = True
            if bird_id.lower() in strategy_file.lower():
                one_bird_centered = True
                multiple_bird_centered = False

            if multiple_bird_centered or one_bird_centered or row['strategy_present'] == True:
                json_results = format_using_gpt(toc, bird_name, multiple_bird_centered)
                if json_results:
                    for key, value in json_results.items():
                        row[key] = value
                    row['Analyze_by_sisukord'] = True
                    results.append(row)
            else:
                non_bird_strategy_texts = extract_bird_sections(text, bird_name)
                row['Kokkuvõte_text'] = non_bird_strategy_texts
                row['Analyze_by_sisukord'] = False
                results.append(row)
        elif not toc and bird_id.lower() in strategy_file.lower():
            row['Kokkuvõte_text'] = text
            row['Analyze_by_sisukord'] = False
            results.append(row)
        else:
            non_bird_strategy_texts = extract_bird_sections(text, bird_name)
            row['Kokkuvõte_text'] = non_bird_strategy_texts
            row['Analyze_by_sisukord'] = False
            results.append(row)


    result_df = pd.DataFrame(results)
    result_df.to_csv("sample_output.csv", index=False, encoding='utf-8')


if __name__ == '__main__':
    main()
