import json
import pandas as pd
from pathlib import Path

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "records.json"


def main():
    with open(DATA_PATH, "r", encoding="utf-8") as file:
        records = json.load(file)

    if not records:
        print("No records found.")
        return

    df = pd.DataFrame(records)

    print("\n--- PyDocsPal Data Analysis ---")

    # Fact 1: Total records
    print(f"\n1. Total records: {len(df)}")

    # Fact 2: Records by category
    print("\n2. Records by kind:")
    print(df["kind"].value_counts().to_string())

    # Fact 3: Most represented modules
    print("\n3. Records by module:")
    print(df["module"].value_counts().head(5).to_string())


if __name__ == "__main__":
    main()