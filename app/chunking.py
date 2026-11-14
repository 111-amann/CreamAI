
from pathlib import Path
from collections import Counter
import re


# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "extracted"
    / "python-3.15-docs-text"
)

# Chunking configuration
CHUNK_SIZE = 1800
CHUNK_OVERLAP = 250

# Common reStructuredText heading underline characters
HEADING_CHARS = {"*", "=", "-", "~", "^", "#", "+", '"'}


def is_heading_underline(line: str) -> bool:
    """Check whether a line looks like a reStructuredText heading underline."""
    stripped = line.strip()

    if len(stripped) < 2:
        return False

    if len(set(stripped)) != 1:
        return False

    return stripped[0] in HEADING_CHARS


def extract_title(lines: list[str], fallback: str) -> str:
    """Extract the document title from its first few lines."""
    for index in range(min(5, len(lines) - 1)):
        title = lines[index].strip()
        underline = lines[index + 1].strip()

        if (
            title
            and is_heading_underline(underline)
            and len(underline) >= len(title)
        ):
            return title

    return fallback


def split_text(
    text: str,
    chunk_size: int = CHUNK_SIZE,
    overlap: int = CHUNK_OVERLAP,
) -> list[str]:
    """Split text into overlapping chunks, preferring paragraph boundaries."""
    text = text.strip()

    if not text:
        return []

    if overlap >= chunk_size:
        raise ValueError("Overlap must be smaller than chunk size.")

    chunks = []
    start = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Prefer splitting at a paragraph boundary.
        if end < len(text):
            split_at = text.rfind("\n\n", start, end)

            if split_at > start:
                end = split_at

        chunk = text[start:end].strip()

        if chunk:
            chunks.append(chunk)

        if end >= len(text):
            break

        # Move forward while retaining overlap.
        next_start = max(end - overlap, start + 1)

        # Avoid starting in the middle of a word where possible.
        while (
            next_start < len(text)
            and not text[next_start].isspace()
        ):
            next_start += 1

        start = next_start

    return chunks


def extract_sections(text: str) -> list[tuple[str, str]]:
    """
    Split a reStructuredText-style document into sections.

    Returns:
        List of (section_title, section_text) tuples.
    """
    lines = text.splitlines()

    sections = []
    current_section = "Introduction"
    current_lines = []

    index = 0

    while index < len(lines):
        line = lines[index]

        # A heading is usually followed by a repeated punctuation underline.
        if (
            line.strip()
            and index + 1 < len(lines)
            and is_heading_underline(lines[index + 1])
            and len(lines[index + 1].strip()) >= len(line.strip())
        ):
            section_text = "\n".join(current_lines).strip()

            if section_text:
                sections.append((current_section, section_text))

            current_section = line.strip()

            # Keep the heading line. The underline is added by the next loop.
            current_lines = [line]

            index += 1
            continue

        current_lines.append(line)
        index += 1

    # Save the final section.
    section_text = "\n".join(current_lines).strip()

    if section_text:
        sections.append((current_section, section_text))

    return sections


def chunk_document(file_path: Path) -> list[dict]:
    """Read one documentation file and convert it into chunks."""
    text = file_path.read_text(
        encoding="utf-8",
        errors="ignore",
    )

    lines = text.splitlines()

    document_title = extract_title(
        lines,
        fallback=file_path.stem.replace("_", " ").title(),
    )

    sections = extract_sections(text)

    chunks = []
    chunk_index = 0

    relative_source = str(
        file_path.relative_to(PROJECT_ROOT)
    )

    for section_title, section_text in sections:
        section_chunks = split_text(section_text)

        for chunk_text in section_chunks:
            chunks.append(
                {
                    "id": f"{file_path.stem}_{chunk_index}",
                    "text": chunk_text,
                    "source": relative_source,
                    "page": "unknown",
                    "title": document_title,
                    "section": section_title,
                    "chunk_index": chunk_index,
                }
            )

            chunk_index += 1

    return chunks


def load_all_chunks() -> list[dict]:
    """Load and chunk all extracted Python documentation text files."""
    if not DOCS_DIR.exists():
        raise FileNotFoundError(
            f"Documentation directory not found: {DOCS_DIR}"
        )

    all_chunks = []

    text_files = sorted(DOCS_DIR.rglob("*.txt"))

    for file_path in text_files:
        try:
            document_chunks = chunk_document(file_path)
            all_chunks.extend(document_chunks)

        except OSError as exc:
            print(f"Could not read {file_path}: {exc}")

    return all_chunks


if __name__ == "__main__":
    chunks = load_all_chunks()

    print(f"Total chunks created: {len(chunks)}")

    if not chunks:
        print("No chunks were created. Check the documentation directory.")
        raise SystemExit(1)

    print("\nFirst chunk metadata:")
    print(
        {
            key: value
            for key, value in chunks[0].items()
            if key != "text"
        }
    )

    print("\nFirst chunk text:")
    print(chunks[0]["text"][:500])

    print("\nSample section names:")
    for section in list(
        dict.fromkeys(chunk["section"] for chunk in chunks)
    )[:10]:
        print(f"- {section}")

    # Distribution diagnostics
    print("\nChunks by source file (top 10):")

    source_counts = Counter(
        Path(chunk["source"]).name
        for chunk in chunks
    )

    for source, count in source_counts.most_common(10):
        print(f"{source}: {count}")

    print("\nChunks by section (top 10):")

    section_counts = Counter(
        chunk["section"]
        for chunk in chunks
    )

    for section, count in section_counts.most_common(10):
        print(f"{section}: {count}")
