import json
import re
from pathlib import Path


def normalize_company_name(name):
    """
    Normalize recruiter-entered company names for matching.
    """

    if not name:
        return ""

    name = name.strip().lower()

    # Remove punctuation
    name = re.sub(r"[^\w\s]", "", name)

    # Normalize whitespace
    name = re.sub(r"\s+", " ", name)

    return name


def load_company_configs(
    companies_folder="data/private/companies"
):
    """
    Load every company config.json file from the private data folder.
    """

    companies = []

    companies_path = Path(companies_folder)

    if not companies_path.exists():
        return companies

    for config_path in companies_path.rglob("config.json"):
        with open(config_path, "r", encoding="utf-8") as file:
            config = json.load(file)

        company_id = config.get("company_id")
        aliases = config.get("aliases", [])

        if not company_id:
            continue

        normalized_aliases = [
            normalize_company_name(alias)
            for alias in aliases
        ]

        companies.append({
            "company_id": company_id,
            "aliases": normalized_aliases,
            "config_path": str(config_path)
        })

    return companies


def match_company(company_name):
    """
    Match recruiter input against known company aliases.

    Returns the internal company ID if found.
    Returns None if no company matches.
    """

    normalized_input = normalize_company_name(company_name)

    if not normalized_input:
        return None

    companies = load_company_configs()

    for company in companies:
        if normalized_input in company["aliases"]:
            return company["company_id"]

    return None


if __name__ == "__main__":
    test_names = [
        "Gofore",
        "GOFORE",
        "Gofore Oyj",
        "Gofore Plc",
        "  Gofore Oyj  ",
        "Unknown Company"
    ]

    for name in test_names:
        result = match_company(name)

        print(
            f"{name!r} -> {result}"
        )