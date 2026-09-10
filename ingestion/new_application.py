import argparse
import json
import re
import sys
from pathlib import Path


def normalize_company_id(value):
    value = value.strip().lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def company_display_name(company_id):
    return " ".join(
        word.capitalize()
        for word in company_id.split("-")
    )


def write_file(path, content):
    path.write_text(
        content.strip() + "\n",
        encoding="utf-8"
    )


def create_application(company_id, display_name=None):
    company_id = normalize_company_id(company_id)

    if not company_id:
        raise ValueError(
            "Company ID cannot be empty."
        )

    if display_name:
        display_name = display_name.strip()
    else:
        display_name = company_display_name(company_id)

    project_root = Path(__file__).resolve().parents[1]

    company_folder = (
        project_root
        / "data"
        / "private"
        / "companies"
        / company_id
    )

    if company_folder.exists():
        raise FileExistsError(
            f"Company folder already exists: {company_folder}"
        )

    company_folder.mkdir(parents=True)

    config = {
        "company_id": company_id,
        "aliases": [
            display_name
        ]
    }

    config_path = company_folder / "config.json"
    config_path.write_text(
        json.dumps(
            config,
            indent=2,
            ensure_ascii=False
        ) + "\n",
        encoding="utf-8"
    )

    company_info = f"""
TITLE: {display_name} Company Information
COMPANY_ID: {company_id}
DOCUMENT_TYPE: company
SOURCE:
SOURCE_URL:

---

Replace this text with relevant information about {display_name}.

Suggested information:
- What the company does
- Main services or products
- Technologies and areas of expertise
- Company values or working culture
- Relevant AI, cloud, software or automation activities
- Information especially relevant to the position you applied for
"""

    position_info = f"""
TITLE: {display_name} Position Information
COMPANY_ID: {company_id}
DOCUMENT_TYPE: position
SOURCE:
SOURCE_URL:

---

Replace this text with the job posting information.

Suggested information:
- Position title
- Main responsibilities
- Required skills
- Preferred skills
- Technologies
- Experience requirements
- Cloud / AI / software requirements
- Language requirements
- Location and working model
- Other relevant details from the job posting
"""

    applicant_match = f"""
TITLE: Miika's Fit for {display_name}
COMPANY_ID: {company_id}
DOCUMENT_TYPE: applicant_match
SOURCE: Applicant analysis
SOURCE_URL:

---

Analyze Miika's suitability for this specific position.

Strong matches:
- Add verified strengths that directly match the position.

Relevant professional experience:
- Add relevant professional experience from the CV.

Relevant projects and independent learning:
- Add relevant AI, RAG, automation, cloud or software projects.

Developing areas:
- Add skills that are currently being developed.

Gaps / not established:
- Add requirements from the position that are not demonstrated by
  Miika's CV, projects, certifications or professional experience.

Overall fit:
- Write a short, factual assessment without exaggerating experience.
"""

    write_file(
        company_folder / "company_info.txt",
        company_info
    )

    write_file(
        company_folder / "position_info.txt",
        position_info
    )

    write_file(
        company_folder / "applicant_match.txt",
        applicant_match
    )

    print()
    print("Work Application Assistant — New Application")
    print("=" * 48)
    print(f"Company:    {display_name}")
    print(f"Company ID: {company_id}")
    print()
    print("Created:")
    print(f"  ✓ {company_folder}")
    print("  ✓ config.json")
    print("  ✓ company_info.txt")
    print("  ✓ position_info.txt")
    print("  ✓ applicant_match.txt")
    print()
    print("Next steps:")
    print("  1. Add company aliases to config.json if needed.")
    print("  2. Fill company_info.txt.")
    print("  3. Fill position_info.txt.")
    print("  4. Fill applicant_match.txt.")
    print("  5. Run:")
    print(
        f"     python -m ingestion.add_application {company_id}"
    )
    print()
    print(
        "The generated files are private application data and "
        "should remain under data/private/."
    )
    print("=" * 48)
    print()


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Create the private folder and document templates "
            "for a new job application."
        )
    )

    parser.add_argument(
        "company_id",
        help=(
            "Stable company ID, for example: nokia "
            "or company-x"
        )
    )

    parser.add_argument(
        "--name",
        dest="display_name",
        help=(
            "Optional display name, for example: "
            "\"Nokia Oyj\""
        )
    )

    args = parser.parse_args()

    try:
        create_application(
            args.company_id,
            args.display_name
        )
    except Exception as exc:
        print()
        print("=" * 48)
        print(f"ERROR: {exc}")
        print("=" * 48)
        print()
        sys.exit(1)


if __name__ == "__main__":
    main()
