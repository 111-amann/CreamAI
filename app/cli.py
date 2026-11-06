
from app.records import load_records, search, count_by, get_by_id


def display_record(record):
    """Display one documentation record."""
    print("\n" + "-" * 55)
    print(f"ID          : {record['id']}")
    print(f"Module      : {record['module']}")
    print(f"Name        : {record['name']}")
    print(f"Kind        : {record['kind']}")
    print(f"Signature   : {record['signature']}")
    print(f"Summary     : {record['summary']}")
    print(f"Version Note: {record['version_note']}")
    print("-" * 55)


def main():
    records = load_records()

    if not records:
        print("No records found. Check data/records.json.")
        return

    while True:
        print("\n========== PyDocsPal ==========")
        print("1. Display all records")
        print("2. Search documentation")
        print("3. Count by category")
        print("4. Get record by ID")
        print("0. Exit")
        print("===============================")

        choice = input("Enter your choice: ").strip()

        if choice == "1":
            for record in records:
                display_record(record)

        elif choice == "2":
            keyword = input("Enter search keyword: ")
            results = search(records, keyword)

            if results:
                print(f"\nFound {len(results)} result(s).")
                for record in results:
                    display_record(record)
            else:
                print("No matching records found.")

        elif choice == "3":
            category = input(
                "Count by (kind/module): "
            ).strip().lower()

            if category not in ["kind", "module"]:
                print("Invalid category.")
                continue

            counts = count_by(records, category)

            print(f"\nCounts by {category}:")
            for key, value in sorted(counts.items()):
                print(f"{key}: {value}")

        elif choice == "4":
            try:
                record_id = int(input("Enter record ID: "))
                record = get_by_id(records, record_id)

                if record:
                    display_record(record)
                else:
                    print("Record not found.")

            except ValueError:
                print("Please enter a valid numeric ID.")

        elif choice == "0":
            print("Thank you for using PyDocsPal!")
            break

        else:
            print("Invalid choice. Try again.")


if __name__ == "__main__":
    main()
