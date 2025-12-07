import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from biodiversity import (
    get_extinct_species,
    parse_EELIS_links,
    EELIS_data,
    get_species_google_strategies,
    prepare_strategy_files,
    extract_and_process_reports,
    extract_birds_info_from_text,
    extract_relevant_sections,
    extract_sections_texts,
    extract_analysis_data,
)


def run_full_pipeline() -> None:
    get_extinct_species()
    parse_EELIS_links()
    EELIS_data()
    get_species_google_strategies()
    prepare_strategy_files()
    extract_and_process_reports()
    extract_birds_info_from_text()
    extract_relevant_sections()
    extract_sections_texts()
    extract_analysis_data()


if __name__ == "__main__":
    run_full_pipeline()
