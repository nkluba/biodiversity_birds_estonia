import re
import os
from openai import OpenAI

openai_api_key = os.getenv('OPENAIKEY')
client = OpenAI(api_key=openai_api_key)


# Function to read text from a file
def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


# Function to extract relevant sections using regex
def extract_veetallaja_sections(text):
    # Regex pattern to find blocks where "veetallaja" is mentioned, capturing the surrounding context
    veetallaja_pattern = re.compile(
        r'(^(?:(?!\n\s*\n).)*\bveetallaja\b(?:(?!\n\s*\n).)*$)',
        re.IGNORECASE | re.MULTILINE | re.DOTALL
    )
    matches = veetallaja_pattern.findall(text)

    # Clean up the extracted sections
    cleaned_matches = [re.sub(r'\s+', ' ', match).strip() for match in matches]
    return cleaned_matches


def format_using_gpt(text):
    prompt = f"Format the following information about 'veetallaja' in a clear and structured manner:\n\n{text}\n\nStructure as follows:\n- Habitat\n- Habitat Condition\n- Population Status/Changes\n- Threats\n- Others (if any)"

    stream = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that helps to format extracted information."},
            {"role": "user", "content": prompt}
        ],
        stream=True
    )

    response_content = ""
    for chunk in stream:
        print(chunk)
        for choice in chunk.choices:
            content = choice.delta.content
            if content is not None:
                response_content += content

    return response_content.strip()


def main():
    # Step 1: Read the text from the file
    file_path = 'strategy_materials/A2%20Paljassaare%20kaitsekorralduskava%2C%20projektiala%2038_cleaned.txt'
    text = read_text_from_file(file_path)

    # Step 2: Extract relevant sections
    veetallaja_matches = extract_veetallaja_sections(text)
    extracted_text = "\n".join(veetallaja_matches)

    # Step 3: Format the extracted information using ChatGPT
    if extracted_text:
        print(format_using_gpt(extracted_text))
    else:
        print("No relevant 'veetallaja' sections found in the text.")


if __name__ == "__main__":
    main()
    # Logic:
    # IF Kirjeldus section filled, extract all vars possible from it; look onto other variables in pdf texts
    # IF not present, but pdf is this bird-centered, extract 'Kokkuvotte part'
    # ELSE process pdf with subset parts mentioning birds in pdf's which do not totally belong to them
