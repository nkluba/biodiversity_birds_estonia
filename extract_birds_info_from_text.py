import re
import os
from transformers import pipeline
from openai import OpenAI
import torch

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


def format_using_gpt(text):
    # Construct the new prompt based on the provided parameters
    prompt = (
        f"Vorminda järgmine teave 'veetallaja' kohta selgel ja struktureeritud viisil:\n\n{text}\n\n"
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
        print(chunk)
        for choice in chunk.choices:
            content = choice.delta.content
            if content is not None:
                response_content += content

    return response_content.strip()


def format_using_llamas(text):
    # Construct the prompt to format the information for 'veetallaja'
    prompt = (
        f"Vorminda järgmine teave 'veetallaja' kohta selgel ja struktureeritud viisil:\n\n{text}\n\n"
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

    # Initialize the text-generation pipeline
    pipe = pipeline("text-generation", model="tartuNLP/Llammas", torch_dtype=torch.bfloat16, device_map="auto")

    # Generate the output using the prompt
    outputs = pipe(prompt, max_new_tokens=256, do_sample=True, temperature=0.6, top_k=50, top_p=0.9)

    # Extract the generated text
    response_content = outputs[0]["generated_text"]

    # Return the processed text
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
        #print(format_using_llamas(extracted_text))
    else:
        print("No relevant 'veetallaja' sections found in the text.")


if __name__ == "__main__":
    main()
    # Logic:
    # IF Kirjeldus section filled, extract all vars possible from it; look onto other variables in pdf texts
    # IF not present, but pdf is this bird-centered, extract 'Kokkuvotte part'
    # ELSE process pdf with subset parts mentioning birds in pdf's which do not totally belong to them
