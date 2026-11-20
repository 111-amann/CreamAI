"""
app/tools.py - Deterministic Standard Library Version Compatibility Tool for PyDocsPal.

Provides:
- Ingestion-time version metadata extraction from Python documentation corpus.
- CSV generation and rebuilding (data/stdlib_versions.csv).
- Deterministic stdlib_version_check tool.
"""

import argparse
import csv
import re
from pathlib import Path
from typing import Any, Optional

from packaging.version import parse as parse_version

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DOCS_DIR = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "extracted"
    / "python-3.15-docs-text"
)
DEFAULT_CSV_PATH = PROJECT_ROOT / "data" / "stdlib_versions.csv"

KNOWN_CLASS_MODULES = {
    "Path": "pathlib",
    "PurePath": "pathlib",
    "PurePosixPath": "pathlib",
    "PureWindowsPath": "pathlib",
    "Counter": "collections",
    "defaultdict": "collections",
    "deque": "collections",
    "ChainMap": "collections",
    "OrderedDict": "collections",
    "UserDict": "collections",
    "UserList": "collections",
    "UserString": "collections",
    "Popen": "subprocess",
    "CompletedProcess": "subprocess",
    "ArgumentParser": "argparse",
    "Namespace": "argparse",
    "Process": "multiprocessing",
    "Queue": "queue",
    "PriorityQueue": "queue",
    "LifoQueue": "queue",
    "SimpleQueue": "queue",
}


def clean_text(text: str) -> str:
    """Normalize whitespace and punctuation in evidence strings."""
    return re.sub(r"\s+", " ", text).strip()


def parse_py_version(v_str: str):
    """Reliably parse a Python version string for comparisons.
    
    Returns a packaging.version.Version object for valid versions,
    or raises ValueError for invalid versions.
    """
    clean = re.sub(r"[^0-9\.]", "", str(v_str)).strip(".")
    
    # Validate that we have at least one digit part
    if not clean or not any(c.isdigit() for c in clean):
        raise ValueError(f"Invalid version string: '{v_str}'")
    
    try:
        return parse_version(clean)
    except Exception as exc:
        raise ValueError(f"Invalid version string: '{v_str}'") from exc


def normalize_symbol(symbol: str) -> str:
    """Normalize symbol string by stripping decorators, parens, and spaces."""
    s = symbol.strip()
    if s.startswith("@"):
        s = s[1:]
    if s.endswith("()"):
        s = s[:-2]
    return s.strip()


def qualify_symbol(raw_sym: str, default_module: str = "") -> tuple[str, str]:
    """
    Resolve a symbol name into a (fully_qualified_symbol, module) tuple.
    """
    sym = raw_sym.strip().lstrip(".")
    if "." in sym:
        parts = sym.split(".")
        first = parts[0]
        if first in KNOWN_CLASS_MODULES:
            mod = KNOWN_CLASS_MODULES[first]
            return f"{mod}.{sym}", mod
        else:
            return sym, first
    else:
        if sym in KNOWN_CLASS_MODULES:
            mod = KNOWN_CLASS_MODULES[sym]
            return f"{mod}.{sym}", mod
        mod = default_module or "unknown"
        return (f"{mod}.{sym}" if mod != "unknown" else sym), mod


def extract_from_library_file(fpath: Path, docs_dir: Path) -> list[dict]:
    """Extract version directives and associated API symbols from a library doc file."""
    module_name = fpath.stem
    rel_path = str(fpath.relative_to(docs_dir)).replace("\\", "/")
    text = fpath.read_text(encoding="utf-8", errors="ignore")
    lines = text.splitlines()
    records = []

    # 1. Top-level module addition
    for i in range(min(20, len(lines))):
        m_mod_add = re.search(
            r"\bAdded in (?:Python\s+)?version\s+([0-9]+(?:\.[0-9]+)+)",
            lines[i],
            re.I,
        )
        if m_mod_add:
            records.append({
                "symbol": module_name,
                "module": module_name,
                "event_type": "added",
                "version": m_mod_add.group(1),
                "source_file": rel_path,
                "evidence": clean_text(lines[i]),
            })
            break

    current_class = None
    current_symbol = None

    for line in lines:
        line_clean = line.strip()
        if not line_clean:
            continue

        # Class / Exception declaration
        m_cls = re.match(r"^(?:class|exception)\s+([a-zA-Z_][\w\.]*)\s*(?:\(.*\))?:?$", line)
        if m_cls:
            raw_cls = m_cls.group(1)
            if "." in raw_cls:
                parts = raw_cls.split(".")
                current_class = parts[-1]
                current_symbol = raw_cls
            else:
                current_class = raw_cls
                current_symbol = f"{module_name}.{raw_cls}"
            continue

        # Decorator: @module.func or @func
        m_dec = re.match(r"^@([a-zA-Z_][\w\.]*)\s*(?:\(.*\))?$", line)
        if m_dec:
            raw_dec = m_dec.group(1)
            if raw_dec.startswith(module_name + "."):
                current_symbol = raw_dec
            elif "." in raw_dec:
                current_symbol = raw_dec
            else:
                current_symbol = f"{module_name}.{raw_dec}"
            continue

        # Function / Method signature at column 0 (unindented)
        if not line.startswith(" ") and not line.startswith("\t"):
            m_func = re.match(r"^([a-zA-Z_][\w\.]*)\s*\((.*?)\)\s*$", line)
            if m_func:
                raw_name = m_func.group(1)
                if raw_name not in {"for", "if", "while", "return", "yield", "see", "note"}:
                    if raw_name.startswith(module_name + "."):
                        current_symbol = raw_name
                    elif "." in raw_name:
                        parts = raw_name.split(".")
                        current_class = parts[0]
                        current_symbol = f"{module_name}.{raw_name}"
                    else:
                        if current_class:
                            current_symbol = f"{module_name}.{current_class}.{raw_name}"
                        else:
                            current_symbol = f"{module_name}.{raw_name}"
                    continue

        sym = current_symbol or module_name

        # Deprecated since X, removed in Y
        m_dep_rem = re.search(
            r"Deprecated since (?:Python\s+)?version\s+([0-9]+(?:\.[0-9]+)+)[,\s]+(?:will be removed in|removed in)(?:\s+version)?\s+([0-9]+(?:\.[0-9]+)+)",
            line_clean,
            re.I,
        )
        if m_dep_rem:
            dep_v, rem_v = m_dep_rem.group(1), m_dep_rem.group(2)
            ev = clean_text(line_clean)
            records.append({
                "symbol": sym,
                "module": module_name,
                "event_type": "deprecated",
                "version": dep_v,
                "source_file": rel_path,
                "evidence": ev,
            })
            records.append({
                "symbol": sym,
                "module": module_name,
                "event_type": "removed",
                "version": rem_v,
                "source_file": rel_path,
                "evidence": ev,
            })
            continue

        # Deprecated since version X
        m_dep = re.search(r"Deprecated since (?:Python\s+)?version\s+([0-9]+(?:\.[0-9]+)+)", line_clean, re.I)
        if m_dep:
            records.append({
                "symbol": sym,
                "module": module_name,
                "event_type": "deprecated",
                "version": m_dep.group(1),
                "source_file": rel_path,
                "evidence": clean_text(line_clean),
            })
            continue

        # Removed in version X
        m_rem = re.search(r"Removed in (?:Python\s+)?version\s+([0-9]+(?:\.[0-9]+)+)", line_clean, re.I)
        if m_rem:
            records.append({
                "symbol": sym,
                "module": module_name,
                "event_type": "removed",
                "version": m_rem.group(1),
                "source_file": rel_path,
                "evidence": clean_text(line_clean),
            })
            continue

        # Added in version X
        m_add = re.search(r"Added in (?:Python\s+)?version\s+([0-9]+(?:\.[0-9]+)+)", line_clean, re.I)
        if m_add:
            records.append({
                "symbol": sym,
                "module": module_name,
                "event_type": "added",
                "version": m_add.group(1),
                "source_file": rel_path,
                "evidence": clean_text(line_clean),
            })
            continue

        # Changed in version X
        m_chg = re.search(r"Changed in (?:Python\s+)?version\s+([0-9]+(?:\.[0-9]+)+)", line_clean, re.I)
        if m_chg:
            records.append({
                "symbol": sym,
                "module": module_name,
                "event_type": "changed",
                "version": m_chg.group(1),
                "source_file": rel_path,
                "evidence": clean_text(line_clean),
            })
            continue

    return records


def extract_from_whatsnew(docs_dir: Path) -> list[dict]:
    """Extract removal, deprecation, and addition notes from whatsnew files."""
    whatsnew_dir = docs_dir / "whatsnew"
    records = []
    if not whatsnew_dir.exists():
        return records

    for fpath in sorted(whatsnew_dir.glob("3.*.txt")):
        target_version = fpath.stem
        rel_path = str(fpath.relative_to(docs_dir)).replace("\\", "/")
        text = fpath.read_text(encoding="utf-8", errors="ignore")
        lines = text.splitlines()

        current_module = None
        in_removed_section = False
        in_deprecated_section = False

        for i, line in enumerate(lines):
            line_s = line.strip()
            if not line_s:
                continue

            if line_s == "Removed" and i + 1 < len(lines) and lines[i + 1].startswith("="):
                in_removed_section = True
                in_deprecated_section = False
                current_module = None
                continue
            elif line_s == "Deprecated" and i + 1 < len(lines) and lines[i + 1].startswith("="):
                in_deprecated_section = True
                in_removed_section = False
                current_module = None
                continue
            elif in_removed_section or in_deprecated_section:
                if i + 1 < len(lines) and lines[i + 1].startswith("=") and len(lines[i + 1].strip()) >= 5:
                    if line_s not in ("Removed", "Deprecated"):
                        in_removed_section = False
                        in_deprecated_section = False
                        current_module = None
                        continue

            if (in_removed_section or in_deprecated_section) and i + 1 < len(lines) and lines[i + 1].startswith("-") and len(lines[i + 1].strip()) >= 3:
                current_module = line_s
                continue

            # Removed deprecated "symbol"
            m_rem = re.search(
                r"Removed\s+deprecated\s+[\"\'\`]?([a-zA-Z_][\w\.]*)\s*(?:\(\))?[\"\'\`]?",
                line_s,
                re.I,
            )
            if m_rem:
                raw_sym = m_rem.group(1)
                sym, mod = qualify_symbol(raw_sym, current_module or "")
                records.append({
                    "symbol": sym,
                    "module": mod,
                    "event_type": "removed",
                    "version": target_version,
                    "source_file": rel_path,
                    "evidence": clean_text(line_s),
                })
                if "PurePath" in sym:
                    records.append({
                        "symbol": sym.replace("PurePath", "Path"),
                        "module": mod,
                        "event_type": "removed",
                        "version": target_version,
                        "source_file": rel_path,
                        "evidence": clean_text(line_s),
                    })
                continue

            # Deprecate "symbol", to be removed in Python X.Y
            m_dep_rem = re.search(
                r"Deprecate\s+[\"\'\`]?\.?([a-zA-Z_][\w\.]*)\s*(?:\(\))?[\"\'\`]?[,\s]+to be removed in Python\s+([0-9]+(?:\.[0-9]+)+)",
                line_s,
                re.I,
            )
            if m_dep_rem:
                raw_sym, rem_v = m_dep_rem.group(1), m_dep_rem.group(2)
                sym, mod = qualify_symbol(raw_sym, current_module or "")
                records.append({
                    "symbol": sym,
                    "module": mod,
                    "event_type": "deprecated",
                    "version": target_version,
                    "source_file": rel_path,
                    "evidence": clean_text(line_s),
                })
                records.append({
                    "symbol": sym,
                    "module": mod,
                    "event_type": "removed",
                    "version": rem_v,
                    "source_file": rel_path,
                    "evidence": clean_text(line_s),
                })
                if "PurePath" in sym:
                    records.append({
                        "symbol": sym.replace("PurePath", "Path"),
                        "module": mod,
                        "event_type": "deprecated",
                        "version": target_version,
                        "source_file": rel_path,
                        "evidence": clean_text(line_s),
                    })
                    records.append({
                        "symbol": sym.replace("PurePath", "Path"),
                        "module": mod,
                        "event_type": "removed",
                        "version": rem_v,
                        "source_file": rel_path,
                        "evidence": clean_text(line_s),
                    })
                continue

            # "symbol" has been deprecated since Python X.Y
            m_dep_since = re.search(
                r"[\"\'\`]?\.?([a-zA-Z_][\w\.]*)\s*(?:\(\))?[\"\'\`]?\s+has been deprecated since Python\s+([0-9]+(?:\.[0-9]+)+)",
                line_s,
                re.I,
            )
            if m_dep_since:
                raw_sym, dep_v = m_dep_since.group(1), m_dep_since.group(2)
                sym, mod = qualify_symbol(raw_sym, current_module or "")
                records.append({
                    "symbol": sym,
                    "module": mod,
                    "event_type": "deprecated",
                    "version": dep_v,
                    "source_file": rel_path,
                    "evidence": clean_text(line_s),
                })
                if "PurePath" in sym:
                    records.append({
                        "symbol": sym.replace("PurePath", "Path"),
                        "module": mod,
                        "event_type": "deprecated",
                        "version": dep_v,
                        "source_file": rel_path,
                        "evidence": clean_text(line_s),
                    })
                continue

    return records


def build_stdlib_versions_csv(
    docs_dir: Optional[Path] = None,
    output_path: Optional[Path] = None,
) -> int:
    """
    Extract version notes across the documentation corpus and write data/stdlib_versions.csv.
    Returns the number of unique records saved.
    """
    target_docs_dir = docs_dir or DEFAULT_DOCS_DIR
    target_output_path = output_path or DEFAULT_CSV_PATH

    if not target_docs_dir.exists():
        raise FileNotFoundError(f"Documentation directory not found: {target_docs_dir}")

    library_dir = target_docs_dir / "library"
    all_records = []

    if library_dir.exists():
        for f in sorted(library_dir.glob("*.txt")):
            all_records.extend(extract_from_library_file(f, target_docs_dir))

    all_records.extend(extract_from_whatsnew(target_docs_dir))

    # Deduplicate while preserving different events
    seen = set()
    unique_records = []
    for r in all_records:
        key = (r["symbol"], r["module"], r["event_type"], r["version"], r["evidence"])
        if key not in seen:
            seen.add(key)
            unique_records.append(r)

    target_output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["symbol", "module", "event_type", "version", "source_file", "evidence"]
    with open(target_output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(unique_records)

    return len(unique_records)


class StdlibVersionChecker:
    """Deterministic standard-library version compatibility checker backed by CSV."""

    def __init__(self, csv_path: Optional[Path] = None):
        self.csv_path = csv_path or DEFAULT_CSV_PATH
        self.records: list[dict] = []
        self.by_symbol: dict[str, list[dict]] = {}
        self.module_introduced: dict[str, str] = {}
        self._load()

    def _load(self):
        if not self.csv_path.exists():
            return
        with open(self.csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                self.records.append(row)
                sym = row["symbol"].strip().lower()
                self.by_symbol.setdefault(sym, []).append(row)
                if row["event_type"] == "added" and row["symbol"].lower() == row["module"].lower():
                    self.module_introduced[row["module"].lower()] = row["version"]

    def find_matching_records(self, symbol: str) -> tuple[str, list[dict]]:
        clean = normalize_symbol(symbol).lower()

        # 1. Exact match
        if clean in self.by_symbol:
            return self.by_symbol[clean][0]["symbol"], self.by_symbol[clean]

        # 2. Qualified prefix match (e.g. "Path.mkdir" -> "pathlib.Path.mkdir")
        for stored_sym, rows in self.by_symbol.items():
            if stored_sym.endswith("." + clean):
                return rows[0]["symbol"], rows

        # 3. PurePath vs Path aliasing
        if "purepath." in clean:
            alt = clean.replace("purepath.", "path.")
            if alt in self.by_symbol:
                return self.by_symbol[alt][0]["symbol"], self.by_symbol[alt]
        elif "path." in clean:
            alt = clean.replace("path.", "purepath.")
            if alt in self.by_symbol:
                return self.by_symbol[alt][0]["symbol"], self.by_symbol[alt]

        return symbol, []

    def check(self, symbol: str, python_version: str) -> dict[str, Any]:
        """Check compatibility of a symbol for a specified Python version."""
        matched_symbol, rows = self.find_matching_records(symbol)
        
        # Validate Python version early
        try:
            req_ver = parse_py_version(python_version)
        except ValueError:
            return {
                "symbol": symbol,
                "python_version": python_version,
                "status": "unknown",
                "available": False,
                "introduced_in": None,
                "deprecated_in": None,
                "removed_in": None,
                "relevant_changes": [],
                "source_file": "",
                "evidence": "",
                "message": f"Invalid Python version format: '{python_version}'. Expected format like '3.8' or '3.11'.",
            }

        if not rows:
            return {
                "symbol": symbol,
                "python_version": python_version,
                "status": "unknown",
                "available": False,
                "introduced_in": None,
                "deprecated_in": None,
                "removed_in": None,
                "relevant_changes": [],
                "source_file": "",
                "evidence": "",
                "message": f"No documentation version records found for symbol '{symbol}'.",
            }

        module = rows[0].get("module", "")
        source_file = rows[0].get("source_file", "")

        added = []
        changed = []
        deprecated = []
        removed = []

        for r in rows:
            ev_type = r["event_type"].lower()
            v_str = r["version"]
            v_parsed = parse_py_version(v_str)
            item = (v_parsed, v_str, r)
            if ev_type == "added":
                ev_text = r.get("evidence", "").lower()
                if "parameter" in ev_text or "option" in ev_text or "argument" in ev_text:
                    changed.append(item)
                else:
                    added.append(item)
            elif ev_type == "changed":
                changed.append(item)
            elif ev_type == "deprecated":
                deprecated.append(item)
            elif ev_type == "removed":
                removed.append(item)

        mod_intro_str = self.module_introduced.get(module.lower())
        intro_str = None
        if added:
            added.sort(key=lambda x: x[0])
            intro_str = added[0][1]
        elif mod_intro_str:
            intro_str = mod_intro_str
        elif changed:
            changed.sort(key=lambda x: x[0])
            intro_str = changed[0][1]

        dep_str = None
        if deprecated:
            deprecated.sort(key=lambda x: x[0])
            dep_str = deprecated[0][1]

        rem_str = None
        if removed:
            removed.sort(key=lambda x: x[0])
            rem_str = removed[0][1]

        # Relevant changes for requested version
        relevant_changes = [
            r[2]["evidence"] for r in changed if r[1] == python_version
        ]

        evidence = rows[0]["evidence"]
        for r in rows:
            if r["version"] == python_version:
                evidence = r["evidence"]
                source_file = r["source_file"]
                break

        status = "unknown"
        available = False
        message = ""

        # Version status rules
        if intro_str and req_ver < parse_py_version(intro_str):
            status = "not_yet_available"
            available = False
            message = (
                f"Symbol '{matched_symbol}' was not yet available in Python {python_version} "
                f"(introduced in Python {intro_str})."
            )
        elif rem_str and req_ver >= parse_py_version(rem_str):
            status = "removed"
            available = False
            dep_note = f" (deprecated in Python {dep_str})" if dep_str else ""
            message = (
                f"Symbol '{matched_symbol}' was removed in Python {rem_str}{dep_note} "
                f"and is unavailable in Python {python_version}."
            )
        elif dep_str and req_ver >= parse_py_version(dep_str):
            status = "deprecated"
            available = True
            rem_note = f", scheduled for removal in Python {rem_str}" if rem_str else ""
            message = (
                f"Symbol '{matched_symbol}' is deprecated in Python {python_version} "
                f"(deprecated since Python {dep_str}{rem_note}), but still available."
            )
        elif intro_str and req_ver >= parse_py_version(intro_str):
            status = "available"
            available = True
            message = (
                f"Symbol '{matched_symbol}' is available in Python {python_version} "
                f"(introduced in Python {intro_str})."
            )
        elif not intro_str and changed and req_ver >= parse_py_version(changed[0][1]):
            status = "available"
            available = True
            message = f"Symbol '{matched_symbol}' is documented as available in Python {python_version}."
        else:
            status = "unknown"
            available = False
            message = f"Insufficient version evidence for symbol '{matched_symbol}' in Python {python_version}."

        if relevant_changes:
            message += f" Documented changes in Python {python_version}: " + "; ".join(relevant_changes)

        return {
            "symbol": matched_symbol,
            "python_version": python_version,
            "status": status,
            "available": available,
            "introduced_in": intro_str,
            "deprecated_in": dep_str,
            "removed_in": rem_str,
            "relevant_changes": relevant_changes,
            "source_file": source_file,
            "evidence": evidence,
            "message": message,
        }


_global_checker: Optional[StdlibVersionChecker] = None


def get_version_checker(csv_path: Optional[Path] = None) -> StdlibVersionChecker:
    """Retrieve or initialize the global StdlibVersionChecker instance."""
    global _global_checker
    if _global_checker is None or csv_path is not None:
        target_path = csv_path or DEFAULT_CSV_PATH
        # Automatically build CSV if it does not yet exist
        if not target_path.exists() and DEFAULT_DOCS_DIR.exists():
            build_stdlib_versions_csv(output_path=target_path)
        _global_checker = StdlibVersionChecker(csv_path=target_path)
    return _global_checker


def stdlib_version_check(
    symbol: str,
    python_version: str,
    csv_path: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Deterministic Python standard-library compatibility tool.

    Determines whether a module, class, function, or API is available
    for a specified Python version using the documentation version metadata CSV.
    """
    checker = get_version_checker(csv_path)
    return checker.check(symbol=symbol, python_version=python_version)


def extract_candidate_symbols(
    text: str,
    citations: Optional[list[dict]] = None
) -> list[str]:
    """
    Extract candidate Python standard library symbols from text and citations.
    """
    candidates: list[str] = []

    # 1. Backtick spans: `symbol`
    for m in re.findall(r"`([a-zA-Z_][\w\.]*)`", text):
        if m not in candidates and not m.isdigit():
            candidates.append(m)

    # 2. Dotted identifiers: module.sub.func
    for m in re.findall(r"\b([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)+)\b", text):
        if m.lower() not in {"e.g", "i.e", "etc", "txt", "py", "json"} and m not in candidates:
            candidates.append(m)

    # 3. Known class / module names
    for name in KNOWN_CLASS_MODULES:
        pattern = rf"\b{re.escape(name)}\b"
        if re.search(pattern, text) and name not in candidates:
            candidates.append(name)

    # 4. From citations: section and source
    if citations:
        for c in citations:
            sec = c.get("section", "")
            if sec and sec != "unknown":
                for part in re.findall(r"\b([a-zA-Z_][\w\.]*)\b", sec):
                    if part not in candidates and len(part) > 1 and not part.isdigit():
                        candidates.append(part)
            src = c.get("source", "")
            if "library/" in src:
                mod_name = Path(src).stem
                if mod_name not in candidates:
                    candidates.append(mod_name)

    return candidates


def detect_compatibility_info(
    question: str,
    answer: str = "",
    python_version: str = "3.12",
    citations: Optional[list[dict]] = None,
    csv_path: Optional[Path] = None,
) -> dict[str, Any]:
    """
    Detect Python standard library symbols in question, answer, and citations,
    and return structured compatibility information for the specified Python version.
    """
    checker = get_version_checker(csv_path)
    combined_text = f"{question}\n{answer}"
    candidates = extract_candidate_symbols(combined_text, citations)

    compat_info: dict[str, Any] = {
        "has_version_check": False,
        "checks": [],
        "warnings": [],
    }

    seen_symbols: set[str] = set()
    found_known = False

    for cand in candidates:
        matched_sym, rows = checker.find_matching_records(cand)
        if rows:
            clean_sym = matched_sym.lower()
            if clean_sym in seen_symbols:
                continue
            seen_symbols.add(clean_sym)

            res = checker.check(cand, python_version)
            if res.get("status") != "unknown" or res.get("introduced_in") or res.get("deprecated_in") or res.get("removed_in"):
                found_known = True
                compat_info["checks"].append({
                    "symbol": res["symbol"],
                    "status": res["status"],
                    "available": res["available"],
                    "introduced_in": res.get("introduced_in"),
                    "deprecated_in": res.get("deprecated_in"),
                    "removed_in": res.get("removed_in"),
                    "evidence": res.get("evidence", ""),
                    "source_file": res.get("source_file", ""),
                })

                status = res.get("status")
                dep_in = res.get("deprecated_in")
                rem_in = res.get("removed_in")
                sym_name = res["symbol"]

                if status == "deprecated" and dep_in:
                    warn = f"⚠️ `{sym_name}` - Deprecated since Python {dep_in}"
                    if rem_in:
                        warn += f", scheduled for removal in Python {rem_in}"
                    if warn not in compat_info["warnings"]:
                        compat_info["warnings"].append(warn)
                elif status == "removed" and rem_in:
                    warn = f"❌ `{sym_name}` - Removed in Python {rem_in}"
                    if warn not in compat_info["warnings"]:
                        compat_info["warnings"].append(warn)

    if found_known:
        compat_info["has_version_check"] = True
    elif candidates:
        # Candidate symbol detected but not in stdlib versions CSV -> unknown status
        primary_sym = candidates[0]
        compat_info["has_version_check"] = True
        compat_info["checks"].append({
            "symbol": primary_sym,
            "status": "unknown",
            "available": False,
            "introduced_in": None,
            "deprecated_in": None,
            "removed_in": None,
            "evidence": "",
            "source_file": "",
        })

    return compat_info


def main():
    parser = argparse.ArgumentParser(description="PyDocsPal Standard Library Version Tool")
    parser.add_argument("--rebuild-csv", action="store_true", help="Rebuild data/stdlib_versions.csv from docs")
    parser.add_argument("--symbol", type=str, help="API symbol to check (e.g. pathlib.Path.mkdir)")
    parser.add_argument("--python-version", type=str, help="Python version to check (e.g. 3.8)")
    args = parser.parse_args()

    if args.rebuild_csv or not DEFAULT_CSV_PATH.exists():
        print(f"Rebuilding standard library versions CSV at {DEFAULT_CSV_PATH}...")
        count = build_stdlib_versions_csv()
        print(f"Successfully generated {count} records in {DEFAULT_CSV_PATH}")

    if args.symbol and args.python_version:
        res = stdlib_version_check(args.symbol, args.python_version)
        print("\nResult:")
        for k, v in res.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()

