import csv
import os
from openai import OpenAI

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAIAPIKEY')
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
    # Add bird_name-specific handling to the prompt to ensure the correct sections are highlighted
    prompt = (
        f"Kasutades järgnevat sisukorda:\n\n{toc}\n\n"
        f"Palun lahenda ja tagasta JSON formaadis need osad, mis on seotud järgmiste teemadega ainult "
        f"linnule {bird_name[:-3] if bird_name else ''}: "
        "'Elupaik', 'Elupaiga seisund', 'Ohud', "
        "'Populatsiooni muutused Eestis', 'Uuringud', 'Seisund ELis', 'Kokkuvõte'."
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
    return json_response

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
            bird_id = bird_name[:-3]  # this removes the last 3 characters (e.g., '(XX)')

            text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '_cleaned.txt'))
            if bird_id.lower() in strategy_file.lower():
                # File contains data for one bird (bird_id in the file name)
                text = read_text_from_file(text_file_path)
                toc = extract_table_of_contents(text)
                if toc:
                    json_results = format_using_gpt(toc, bird_name)
                    row.update(json_results)  # Assuming json_results is a dict
                    results.append(row)
            else:
                # Check if file contains data for multiple birds
                text = read_text_from_file(text_file_path)
                toc = extract_table_of_contents(text)
                if toc and bird_id.lower() in toc.lower():
                    json_results = format_using_gpt(toc, bird_name)
                    row.update(json_results)  # Assuming json_results is a dict
                    results.append(row)

    save_to_csv(results)

if __name__ == '__main__':
    main()
