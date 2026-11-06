
# PyDocsPal - Day 1 CLI Menu

print("\nWelcome to PyDocsPal!")

while True:

    print("\nPyDocsPal Menu")
    print("1. About PyDocsPal")
    print("2. Sample Questions")
    print("3. Check Question Category")
    print("0. Exit")

    choice = input("Enter your choice: ")

    # Option 1: About the product
    if choice == "1":

        print("\nAbout PyDocsPal")
        print("PyDocsPal is a Python documentation assistant.")
        print("It helps developers understand Python APIs,")
        print("function usage and version compatibility.")

    # Option 2: Sample questions
    elif choice == "2":

        print("\nSample Questions")
        print("1. What does collections.Counter do?")
        print("2. How does pathlib.Path.read_text() work?")

    # Option 3: Rule check
    elif choice == "3":

        question = input("\nEnter your Python question: ").lower()

        if "deprecated" in question or "removed" in question:
            print("Category: Deprecation and Removal")

        elif "version" in question or "compatible" in question:
            print("Category: Python Version Compatibility")

        elif "function" in question or "module" in question:
            print("Category: Python API Documentation")

        else:
            print("Category: General Python Question")

    # Option 0: Exit
    elif choice == "0":

        print("\nThank you for using PyDocsPal!")
        print("Goodbye!")
        break

    else:
        print("\nInvalid choice. Please try again.")
