# Biodiversity Birds of Estonia – Data Engineering & AI Analytics Pipeline

End-to-end automated data extraction, document processing, and AI-based text analytics pipeline for endangered bird species in Estonia.
The project integrates government biodiversity registries, PDF strategy documents, OCR, and GPT-based semantic extraction into a unified analytical dataset.

The pipeline operates as a **multi-stage ETL system** orchestrated via a Python runner script and persists all intermediate results as CSV artifacts.

---

## Pipeline Overview

1. Extracts protected vertebrate species list from public biodiversity sources.
2. Searches species in the Estonian environmental registry (EELIS) via Selenium.
3. Harvests structured EELIS metadata per species.
4. Searches and downloads official conservation strategy PDFs.
5. Converts native PDFs to text using `pdftotext`.
6. Applies OCR + LLM cleaning for scanned PDF documents.
7. Detects relevant analytical sections via table of contents parsing.
8. Extracts section-level ecological descriptions.
9. Applies GPT-based semantic normalization:
   * Population state
   * Habitat conditions
   * Threat factors
10. Produces final analytics-ready bird species dataset.

---

## Data Collected

### Species Registry Data

For each bird species:

* Estonian name
* Latin name
* Protection category
* Taxonomic group
* National conservation category
* EELIS registry link

### Strategy & Ecology Data

For each species:

* Official conservation strategy availability
* Habitat description
* Population dynamics
* Threat factor assessment
* Protected areas coverage

### AI-Extracted Analytical Fields

Generated using GPT:

* Normalized population condition summary
* Habitat and ecosystem stability assessment
* Major anthropogenic and ecological risk factors

All data is stored as CSV artifacts for reproducibility and auditability.

---

## Output Structure

All generated datasets follow a staged convention:

* `st1_kaitsekategooria_selgroogsed_loomad.csv`
* `st2_EELIS_kaitsekategooria_selgroogsed_loomad.csv`
* `st3_EELIS_additional_data.csv`
* `st4_pdf_gathered.csv`
* `st5_relevant_pdf_reports.csv`
* `st6_relevant_sections_extracted.csv`
* `st7_texts_prepared_for_analysis.csv`
* `st8_birds_data_extracted.csv`
* `updated_birds_descriptions.csv` (analytics-ready showcase output)

These files represent a **fully traceable data lineage** from raw registry scraping to final enriched analytical dataset.

---

## Runtime Modes

### Full Pipeline Execution

Runs the entire ETL + AI analytics workflow end-to-end.

```bash
cd src
python scripts/run_pipeline.py
```

---

### Individual Step Execution

Each stage can be executed independently via:

```bash
python src/biodiversity/<step_name>.py
```

Example:

```bash
python src/biodiversity/extract_analysis_data.py
```

---

## Fault Tolerance

* Selenium page timeouts handled with explicit waits
* Missing PDF handling with safe fallbacks
* OCR only applied to scanned documents
* GPT error handling with NA fallback injection
* Resume-safe processing through staged CSV outputs
* No destructive overwrites of upstream datasets

---

## Project Structure

```text
.
├── src/
│   ├── scripts/
│   │   └── run_pipeline.py
│   └── src/
│       └── biodiversity/
│           ├── __init__.py
│           ├── get_extinct_species.py
│           ├── parse_EELIS_links.py
│           ├── EELIS_data.py
│           ├── get_species_google_strategies.py
│           ├── prepare_strategy_files.py
│           ├── extract_and_process_reports.py
│           ├── extract_birds_info_from_text.py
│           ├── extract_relevant_sections.py
│           ├── extract_sections_texts.py
│           └── extract_analysis_data.py
├── data/
├── requirements.txt
└── README.md
```

---

## Technical Stack

* Python
* Pandas
* Selenium
* Tesseract OCR
* PyMuPDF
* OpenAI API (GPT-based text normalization)
* Linux CLI tooling (`pdftotext`)
* Modular ETL orchestration via Python packages