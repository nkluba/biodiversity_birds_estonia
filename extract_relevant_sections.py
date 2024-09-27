import csv
import os
from openai import OpenAI

# Initialize OpenAI client
openai_api_key = os.getenv('OPENAIKEY')
client = OpenAI(api_key=openai_api_key)



def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def extract_table_of_contents(text):
    # Assuming that the Table of Contents comes before any content, locate by its title
    start_index = text.find("Sisukord")
    if start_index == -1:
        return None
    end_index = text.find("\n\n", start_index)  # Assuming double newlines mark the end of TOC
    toc = text[start_index:end_index].strip()
    return toc


def format_using_gpt(toc):
    # This part of the code handles sending the TOC to GPT and receiving a JSON response
    prompt = (
        f"Kasutades järgnevat sisukorda:\n\n{toc}\n\n"
        "Palun lahenda selle põhjal ja tagasta JSON formaadis,"
        "mis osad on seotud järgmiste teemadega:\n"
        "  'Elupaik', 'Elupaiga seisund', 'Ohud', "
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
    return json_response


def save_to_csv(data, output_file="output.csv"):
    # Assuming data is a list of dictionaries where keys are column names
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
            text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '_cleaned.txt'))
            text = read_text_from_file(text_file_path)
            toc = extract_table_of_contents(text)
            if toc:
                json_results = format_using_gpt(toc)
                print(json_results)
                row.update(json_results)  # Assuming json_results is a dict
                results.append(row)

    save_to_csv(results)


if __name__ == '__main__':
    main()