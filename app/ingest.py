from app.models import Record
import json
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = BASE_DIR / "data" / "raw" / "extracted"
OUTPUT_FILE = BASE_DIR / "data" / "records.json"

# Start with a small, useful slice of the documentation.
TARGET_MODULES = [
    "collections",
    "itertools",
    "functools",
    "pathlib",
    "json",
    "csv"
]


def clean_text(text):
    """Remove excessive whitespace from documentation text."""
    return re.sub(r"\s+", " ", text).strip()


def detect_kind(signature):
    """Make a basic guess about the API type."""
    signature_lower = signature.lower()

    if signature_lower.startswith("class "):
        return "class"

    if signature_lower.startswith("def "):
        return "function"

    if "(" in signature:
        return "function"

    return "attribute"


def extract_records(file_path, module):
    """Extract a first slice of API-like signatures from one text file."""
    records = []

    try:
        text = file_path.read_text(encoding="utf-8")
        lines = text.splitlines()

        for index, line in enumerate(lines):
            line = line.strip()

            # Look for common Python API declaration patterns.
            if not (
                line.startswith("class ")
                or line.startswith("def ")
                or re.match(r"^[a-zA-Z_][\w.]*\s*\(", line)
            ):
                continue

            signature = clean_text(line)

            if len(signature) > 250:
                continue

            # Use the next non-empty line as a short description.
            summary = ""

            for next_line in lines[index + 1:index + 5]:
                candidate = clean_text(next_line)

                if candidate:
                    summary = candidate
                    break

            # Skip records without useful descriptions.
            if not summary:
                continue

            name_match = re.search(
                r"(?:class|def)\s+([A-Za-z_]\w*)|^([A-Za-z_]\w*)",
                signature
            )

            if not name_match:
                continue

            name = name_match.group(1) or name_match.group(2)

            record = Record(
                id=0,
                module=module,
                name=name,
                kind=detect_kind(signature),
                signature=signature,
                summary=summary[:500],
                version_note="Check the official documentation for version details."
            )

            records.append(record.to_dict())

    except UnicodeDecodeError as error:
        print(f"Encoding error in {file_path}: {error}")

    except OSError as error:
        print(f"Could not read {file_path}: {error}")

    except Exception as error:
        print(f"Unexpected error in {file_path}: {error}")

    return records


def main():
    all_records = []
    record_id = 1

    if not RAW_DIR.exists():
        print("Extracted documentation directory not found.")
        print("Download and extract the ZIP archive first.")
        return

    for module in TARGET_MODULES:
        # Look for the corresponding documentation text file.
        matching_files = list(RAW_DIR.rglob(f"{module}.txt"))

        if not matching_files:
            print(f"Documentation file not found for {module}")
            continue

        for file_path in matching_files:
            try:
                module_records = extract_records(file_path, module)

                for record in module_records:
                    record["id"] = record_id
                    record_id += 1
                    all_records.append(record)

                print(
                    f"{module}: extracted "
                    f"{len(module_records)} records"
                )

            except Exception as error:
                print(f"Skipping {file_path}: {error}")

    try:
        OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

        with OUTPUT_FILE.open("w", encoding="utf-8") as file:
            json.dump(all_records, file, indent=4, ensure_ascii=False)

        print(f"\nSaved {len(all_records)} records to {OUTPUT_FILE}")

    except OSError as error:
        print(f"Could not save records: {error}")


if __name__ == "__main__":
    main()
