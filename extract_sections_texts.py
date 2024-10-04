import difflib
import os
import re
import pandas as pd


### File Handling Functions ###

def read_text_from_file(filepath):
    """
    Reads the text from a file and returns it as a string.
    """
    if os.path.isfile(filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    else:
        print(f"File {filepath} not found.")
        return None


def save_to_csv(df, output_file):
    """
    Saves the given pandas DataFrame to a CSV file.
    """
    df.to_csv(output_file, index=False)
    print(f"Updated DataFrame saved to {output_file}")


### Text Processing Functions ###

def extract_full_table_of_contents(text):
    """
    Extracts the full Table of Contents (Sisukord) from the provided text,
    including multi-page layouts and handling irregular breaks.
    It also returns the start and end line numbers.
    """

    # Locate the start of the "Sisukord" section by keyword
    toc_start_index = text.find("Sisukord")
    if toc_start_index == -1:
        return None, None, None  # No TOC found, return placeholders

    current_index = toc_start_index
    toc_text = ""

    # Regular expression to look for ToC lines that end in dots followed by page numbers
    toc_line_pattern = re.compile(r"\.{5,}\s*\d+$")

    # Track how many lines without '....' separators we've seen in a row
    lines_without_dots = 0
    toc_continues = True

    # Determine the start line by counting lines up to the TOC start index
    pre_toc_lines = text[:toc_start_index].splitlines()
    toc_start_line = len(pre_toc_lines) + 1  # Line number where "Sisukord" is detected

    current_line_number = toc_start_line  # Start tracking from the 'Sisukord' line

    toc_found_lines = []  # To store valid ToC lines
    toc_end_line = toc_start_line  # To store the final line of the ToC

    # Loop over the text block-by-block
    while toc_continues and current_index < len(text):
        # Identify the next form feed (page break) or take rest of the text
        page_break_index = text.find("\f", current_index)
        if page_break_index == -1:
            current_chunk = text[current_index:]
            toc_continues = False
        else:
            current_chunk = text[current_index:page_break_index + 1]
            current_index = page_break_index + 1  # Move index to the text after the page break

        toc_lines = current_chunk.splitlines()
        capture_chunk = ""

        # Iterate through the current chunk's lines to check for ToC format
        for line in toc_lines:
            current_line_number += 1  # Increment line counter

            clean_line = line.strip()  # Clean leading and trailing whitespace

            # Skip completely empty lines
            if not clean_line:
                continue

            if toc_line_pattern.search(line):
                # We have a valid ToC entry
                capture_chunk += line + "\n"
                toc_found_lines.append(current_line_number)
                lines_without_dots = 0  # Reset the counter when a valid line is found
                toc_end_line = current_line_number  # Update the end line as we find valid ToC lines
            else:
                # If the line doesn't look like a ToC entry
                lines_without_dots += 1
                if lines_without_dots > 10:  # End after 10 lines without valid ToC patterns
                    toc_continues = False
                    break

        toc_text += capture_chunk

    # If no valid entries were found, return None
    if not toc_found_lines:
        return None, None, None

    return toc_text.strip(), toc_start_line, toc_end_line


def normalize_and_clean_line(line):
    """
    Cleans up a line by removing excess whitespace, normalizing multiple spaces to one,
    and stripping any unnecessary trailing dots or punctuation.
    """
    # Normalize multiple spaces/tabs down to a single space
    line = re.sub(r'\s+', ' ', line)

    # Trim leading and trailing spaces
    line = line.strip()
    line = line.replace('.', '.').replace(' ', ' ')

    last_alpha_index = -1
    for index, char in enumerate(line):
        if char.isalpha():
            last_alpha_index = index

    # If an alphabetic character is found, slice the string up to and including it
    if last_alpha_index != -1:
        line = line[:last_alpha_index + 1].strip()
    else:
        # In case no alphabetic character is found, return the original line
        line = line.strip()

    return line


def normalize_toc(toc):
    lines = toc.splitlines()
    normalized_lines = [normalize_and_clean_line(line) for line in lines]
    return normalized_lines


def find_section_in_toc(lines, section_name):
    """
    Finds the location of a section in the Table of Contents (ToC) and returns its position in the text.
    We normalize both the ToC lines and the section name for a cleaner match
    and use fuzzy matching to match even in case of small differences.
    """
    # Clean and normalize the section name to be searched
    cleaned_section_name = normalize_and_clean_line(section_name)

    # Iterate over ToC lines and try to find a match with cleaned section name
    for i, line in enumerate(lines):
        if cleaned_section_name.replace('.', '').lower() in line.replace('.', '').lower():
            return i, line

    # If no match found, return None, None indicating failure
    return None, None


def extract_text_between_sections(text, start_section, end_section=None):
    """
    Extracts text between two sections in the text. If end_section is not specified, extracts until the end of the document.
    """
    start_index = text.find(start_section)
    if start_index == -1:
        return None

    if end_section:
        end_index = text.find(end_section, start_index)
        if end_index != -1:
            return text[start_index:end_index].strip()

    # If no end_section is found or not specified, extract till the end
    return text[start_index:].strip()


### Extraction Logic Functions ###

def extract_text_for_sections(text, toc, sections, toc_start_line, toc_end_line):
    """
    Loops through the sections in the ToC and extracts the text for each section.
    Handles cases where multiple sections are provided in one line,
    splitting them by ', ' and then collecting their extracted texts in a dictionary.
    """
    extracted_text = {}

    for i, section in enumerate(sections):
        # Split section names by ', ' to handle cases where multiple sections are provided in one line
        individual_sections = [s.strip() for s in section.split(',')]

        toc_sections_list = normalize_toc(toc)

        for j, individual_section in enumerate(individual_sections):
            # Find the current individual section in the ToC
            section_idx, start_section_line = find_section_in_toc(toc_sections_list, individual_section)
            if not start_section_line:
                print(f"Section '{individual_section}' not found in Table of Contents.")
                continue

            # Check for the next section to mark the end of this section's extraction
            # If it's the last section, there's no next section
            if section_idx + 1 < len(toc_sections_list):
                next_section_line = toc_sections_list[section_idx + 1]
            else:
                # If there's no next section (if this is the last section), set it to None
                next_section_line = None

            removed_toc_text = "\n".join(text.splitlines()[:toc_start_line-1] + text.splitlines()[toc_end_line:])
            # Extract the relevant portion of the text between the current section and the next section
            extracted_chunk = extract_text_between_sections(removed_toc_text.lower(), start_section_line.lower(), next_section_line.lower())
            if extracted_chunk:
                # Add the extracted chunk to the dictionary with the section as the key
                extracted_text[individual_section] = extracted_chunk

    return extracted_text


### CSV Processing Functions ###

def process_row(row, strategy_file_path):
    """
    Processes a single row of the CSV to extract relevant text sections from the corresponding strategy file.
    Concatenates extracted texts for each section list specified in the row.
    """
    sections_dict = {
        'Elupaik': row['Elupaik'],
        'Elupaiga seisund': row['Elupaiga seisund'],
        'Ohud': row['Ohud'],
        'Populatsiooni muutused Eestis': row['Populatsiooni muutused Eestis'],
        'Uuringud': row['Uuringud'],
        'Seisund ELis': row['Seisund ELis'],
        'Kokkuvõte': row['Kokkuvõte']
    }

    # Read text for the current strategy
    text = read_text_from_file(strategy_file_path)

    if text is None:
        return None

    # Extract full Table of Contents
    toc, toc_start_line, toc_end_line = extract_full_table_of_contents(text)
    if not toc:
        print(f"Sisukord not found for {strategy_file_path}.")
        return None

    # Extract text for the sections
    extracted_text = extract_text_for_sections(text, toc, sections_dict.values(), toc_start_line, toc_end_line)

    processed_data = {}

    # Concatenate texts for each required section and store them in the processed_data dictionary
    for section_name, section_text in sections_dict.items():
        individual_sections = [s.strip() for s in section_text.split(',')]
        concatenated_text = "\n".join(extracted_text[s] for s in individual_sections if s in extracted_text)

        # Store concatenated text in a new key such as 'Elupaik_text'
        processed_data[f"{section_name}_text"] = concatenated_text

    return processed_data


def process_csv(input_csv, strategy_materials_folder, output_csv):
    """
    Orchestrates the reading of the CSV, processing of each file, and saving the updated CSV.
    """
    # Load the CSV file
    df = pd.read_csv(input_csv)

    # Iterate over each row in the DataFrame
    for index, row in df.iterrows():
        # Extract the strategy file name and path
        strategy_file = row['strategy_file']
        strategy_file_path = os.path.join(strategy_materials_folder, strategy_file.replace('.pdf', '_cleaned.txt'))

        # Process the row to obtain extracted text
        if row['Analyze_by_sisukord'] == True:
            extracted_text = process_row(row, strategy_file_path)

            if extracted_text:
                # Update the DataFrame with the extracted text for the current row
                for key, value in extracted_text.items():
                    df.at[index, key] = value

    # Save the updated DataFrame to the output CSV file
    df.to_csv(output_csv, index=False)

    print(f"Updated CSV file has been saved to {output_csv}")


### Main Function ###

def main():
    # Define paths
    input_csv = 'sample_output.csv'
    strategy_materials_folder = 'strategy_materials'
    output_csv = 'texts_for_analysis.csv'

    # Process the entire CSV
    process_csv(input_csv, strategy_materials_folder, output_csv)


### Script Entry Point ###

if __name__ == '__main__':
    main()


#do this only for Analyze_by_sisukord = True