
import json
from pathlib import Path


# Project root directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Default records file
DEFAULT_RECORDS_PATH = BASE_DIR / "data" / "records.json"


def load_records(path=DEFAULT_RECORDS_PATH):
    """Load documentation records from a JSON file."""
    try:
        with open(path, "r", encoding="utf-8") as file:
            records = json.load(file)

        if not isinstance(records, list):
            raise ValueError("Records file must contain a list.")

        return records

    except FileNotFoundError:
        print(f"File not found: {path}")
        return []

    except json.JSONDecodeError as error:
        print(f"Invalid JSON: {error}")
        return []


def search(records, keyword):
    """Search records by module, name, kind, signature or summary."""
    keyword = keyword.lower().strip()

    if not keyword:
        return []

    results = []

    for record in records:
        searchable_text = " ".join([
            str(record.get("module", "")),
            str(record.get("name", "")),
            str(record.get("kind", "")),
            str(record.get("signature", "")),
            str(record.get("summary", "")),
            str(record.get("version_note", ""))
        ])

        if keyword in searchable_text.lower():
            results.append(record)

    return results


def count_by(records, category="kind"):
    """Count records grouped by a selected field."""
    counts = {}

    for record in records:
        value = record.get(category, "unknown")
        counts[value] = counts.get(value, 0) + 1

    return counts


def get_by_id(records, record_id):
    """Find a record using its unique ID."""
    for record in records:
        if record.get("id") == record_id:
            return record

    return None
