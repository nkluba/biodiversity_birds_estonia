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
        f"Vorminda järgmine teave selgel ja struktureeritud viisil:\n\n{text}\n\n"
        "Struktuur on järgmine (KUI TEAVE PUUDUP TEKSTIS, JÄÄTA 'NA'):\n"
        "- Elupaik\n"
        "- Elupaiga seisund\n"
        "- Ohud\n"
        "- Populatsiooni muutused (nt suurenenud, vähenenud, sama tase == stabiilne)\n"
        "- Kas rändlinnud\n"
        "- Läbiviidud uuringud\n"
        "- Kavandatud, kuid läbi viimata uuringud (nt programmid koos Venemaaga)\n"
        "- Seisund ELis\n"
        "- Populatsioonitrend teistes ELi riikides (nt mõõdukalt väheneb, mõõdukalt suureneb)"
    )

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "Oled abivalmis assistent, kes aitab ekstraktitud teavet vormindada."},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    response_content = ""
    for chunk in stream:
        for choice in chunk.choices:
            content = choice.delta.content
            if content is not None:
                response_content += content

    return response_content.strip()

# Main processing function
def main():
    # Load the CSV file
    df = pd.read_csv('st5_relevant_pdf_reports.csv')[:5]

    # Container for formatted responses
    formatted_responses = []

    # Process each row in the DataFrame
    for _, row in df.iterrows():
        estonian_name = row['Estonian Name']
        kirjeldus_text = str(row.get('Kirjeldus', '') or '')
        ohutegurite_kirjeldus_text = str(row.get('Ohutegurite kirjeldus', '') or '')

        kirjeldus = kirjeldus_text + ' ' + ohutegurite_kirjeldus_text

        strategy_file = row['strategy_file']

        if kirjeldus.strip():
            # Format the combined 'Kirjeldus' and 'Ohutegurite kirjeldus'
            formatted_text = format_using_gpt(kirjeldus)
        else:
            # Read from the text file converted from PDF
            text_file_path = os.path.join('strategy_materials', strategy_file.replace('.pdf', '.txt'))
            text = read_text_from_file(text_file_path)

            # Extract relevant sections for the bird
            bird_sections = extract_bird_sections(text, estonian_name)
            extracted_text = "\n".join(bird_sections)

            if extracted_text:
                # Format the extracted sections
                formatted_text = format_using_gpt(extracted_text)
            else:
                formatted_text = "No relevant sections found."

        # Append the response to the list
        formatted_responses.append(formatted_text)

    # Insert the formatted responses into a new column in the DataFrame
    df['Formatted Response'] = formatted_responses

    # Save the DataFrame to a new CSV file
    df.to_csv('st5_relevant_pdf_reports_with_responses.csv', index=False)

if __name__ == "__main__":
    main()
