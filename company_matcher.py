import json
import re
from pathlib import Path

import streamlit as st


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


def load_company_configs_from_private_folder(
    companies_folder="data/private/companies"
):
    """
    Load company configs from local private files.

    Used for local development where data/private/ exists.
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
            if alias
        ]

        companies.append({
            "company_id": company_id,
            "aliases": normalized_aliases,
            "source": "private_config",
        })

    return companies


def load_company_configs_from_streamlit_secrets():
    """
    Load company aliases from Streamlit Secrets.

    Expected secrets structure:

    [companies.gofore]
    aliases = ["Gofore", "Gofore Oyj", "Gofore Plc"]

    [companies.etteplan]
    aliases = ["Etteplan", "Etteplan Oyj", "Etteplan Plc"]
    """

    companies = []

    try:
        secrets_companies = st.secrets.get("companies", {})
    except Exception:
        return companies

    for company_id, config in secrets_companies.items():
        aliases = config.get("aliases", [])

        normalized_aliases = [
            normalize_company_name(alias)
            for alias in aliases
            if alias
        ]

        # Also allow the company_id itself as valid input.
        normalized_company_id = normalize_company_name(company_id)

        if normalized_company_id not in normalized_aliases:
            normalized_aliases.append(normalized_company_id)

        companies.append({
            "company_id": company_id,
            "aliases": normalized_aliases,
            "source": "streamlit_secrets",
        })

    return companies


def load_company_configs():
    """
    Load known companies.

    Streamlit Secrets are used first for deployed environments.
    Local private config files are used as a fallback for local development.
    """

    secret_companies = load_company_configs_from_streamlit_secrets()

    if secret_companies:
        return secret_companies

    return load_company_configs_from_private_folder()


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
        "Etteplan",
        "Etteplan Oyj",
        "Etteplan Plc",
        "Unknown Company",
    ]

    for name in test_names:
        result = match_company(name)
        print(f"{name!r} -> {result}")
