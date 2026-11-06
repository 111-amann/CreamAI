
import requests
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
OUTPUT_DIR = BASE_DIR / "data" / "raw" / "fetched"

DOCUMENTS = {
    "collections.html":
        "https://docs.python.org/3/library/collections.html",

    "itertools.html":
        "https://docs.python.org/3/library/itertools.html",

    "functools.html":
        "https://docs.python.org/3/library/functools.html",

    "pathlib.html":
        "https://docs.python.org/3/library/pathlib.html"
}


def download_document(name, url):
    """Download one documentation page and save it locally."""

    try:
        response = requests.get(
            url,
            timeout=(5, 30)
        )

        response.raise_for_status()

        file_path = OUTPUT_DIR / name
        file_path.write_bytes(response.content)

        print(f"Downloaded successfully: {name}")
        return True

    except requests.exceptions.Timeout:
        print(f"Timeout while downloading: {name}")

    except requests.exceptions.HTTPError as error:
        print(f"HTTP error for {name}: {error}")

    except requests.exceptions.RequestException as error:
        print(f"Request failed for {name}: {error}")

    except OSError as error:
        print(f"File saving error for {name}: {error}")

    return False


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    success_count = 0

    for name, url in DOCUMENTS.items():
        if download_document(name, url):
            success_count += 1

    print(
        f"\nDownloaded {success_count} "
        f"out of {len(DOCUMENTS)} documents."
    )


if __name__ == "__main__":
    main()
