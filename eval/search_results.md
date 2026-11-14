# PyDocsPal - Semantic Search Evaluation

## 1. Configuration

| Setting | Value |
|---|---|
| Embedding model | `all-MiniLM-L6-v2` |
| Vector database | ChromaDB |
| Similarity metric | Cosine distance |
| Results per question | 5 |
| Total questions | 10 |
| Chunk size | 1800 characters |
| Chunk overlap | 250 characters |
| Total indexed chunks | 21,012 |

Lower cosine distance indicates greater vector similarity.

**Important:** Cosine distance is not a confidence percentage. A lower distance indicates greater similarity between vectors, but does not guarantee that a result answers the question correctly.

## 2. Search Results and Manual Evaluation

### Q1. What functions are available in the Python collections module?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `library/collections.txt` | Module introduction | 0.2974 | Partially relevant |
| 2 | `library/collections.txt` | Module introduction | 0.3537 | Not relevant |
| 3 | `library/collections.txt` | Module introduction | 0.3608 | Not relevant |
| 4 | `library/collections.txt` | Module introduction | 0.3608 | Not relevant |
| 5 | `library/collections.txt` | Module introduction | 0.3707 | Not relevant |

**Observation:**

All five results point to the introductory description of the collections module. They do not provide a useful listing of the available classes and functions.

**Final assessment:** Failed.

**Notes:** The search retrieves the correct module but not the specific API information requested. A module inventory or keyword-based search may be more suitable.

---

### Q2. What is the purpose of collections.Counter, and how is it used?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `whatsnew/3.15.txt` | collections | 0.4356 | Partially relevant |
| 2 | `library/collections.txt` | Counter objects | 0.4701 | Relevant |
| 3 | `builtins/time-complexity.txt` | list | 0.5102 | Not relevant |
| 4 | `library/collections.txt` | Counter objects | 0.5111 | Relevant |
| 5 | `tutorial/controlflow.txt` | range() Function | 0.5165 | Not relevant |

**Observation:**

The second and fourth results contain useful Counter documentation, including behavior for missing elements, examples, and multiset operations.

However, unrelated results also appear in the top five.

**Final assessment:** Partially successful.

**Notes:** Relevant documentation is retrieved, but ranking needs improvement. Exact API matching and keyword-based retrieval could improve the result order.

---

### Q3. What is the function signature of pathlib.Path.read_text()?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `whatsnew/3.9.txt` | pathlib | 0.3048 | Not relevant |
| 2 | `library/pathlib.txt` | Reading and writing files | 0.3464 | Relevant |
| 3 | `library/importlib.resources.txt` | Functional API | 0.3481 | Not relevant |
| 4 | `whatsnew/3.13.txt` | importlib | 0.3638 | Not relevant |
| 5 | `whatsnew/3.8.txt` | pathlib | 0.3654 | Partially relevant |

**Observation:**

The second result contains the requested signature:

`Path.read_text(encoding=None, errors=None, newline=None)`

The first result is about `Path.readlink()`, not `Path.read_text()`.

**Final assessment:** Partially successful.

**Notes:** The exact documentation is retrieved, but it appears at rank 2. Exact API-name matching could improve ranking.

---

### Q4. How does itertools.combinations() work, and what arguments does it accept?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `howto/functional.txt` | Combinatoric functions | 0.3232 | Partially relevant |
| 2 | `howto/functional.txt` | The itertools module | 0.3419 | Partially relevant |
| 3 | `library/itertools.txt` | Itertool Functions | 0.3474 | Relevant |
| 4 | `howto/functional.txt` | Combinatoric functions | 0.3735 | Relevant |
| 5 | `library/itertools.txt` | Itertools Recipes | 0.3858 | Partially relevant |

**Observation:**

The third result contains the API signature:

`itertools.combinations(iterable, r)`

The fourth result explains how combinations work and includes examples.

**Final assessment:** Successful.

**Notes:** The search retrieves both API documentation and explanatory examples. The exact API reference could ideally rank higher.

---

### Q5. Which Python version introduced functools.cache, and how does it differ from functools.lru_cache?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `whatsnew/3.5.txt` | functools | 0.2481 | Not relevant |
| 2 | `whatsnew/3.3.txt` | functools | 0.2816 | Not relevant |
| 3 | `faq/programming.txt` | How do I cache method calls? | 0.3148 | Partially relevant |
| 4 | `whatsnew/3.3.txt` | PEP 421 | 0.3563 | Not relevant |
| 5 | `whatsnew/3.8.txt` | functools | 0.3595 | Partially relevant |

**Observation:**

The retrieved results discuss `lru_cache` and `cached_property`, but none directly answers when `functools.cache` was introduced or how it differs from `lru_cache`.

**Final assessment:** Failed.

**Notes:** The results demonstrate that semantic similarity alone is insufficient for exact API-version questions. Search should prioritize exact names and version-related documentation.

---

### Q6. What were all the changes made to the pathlib module in Python 3.15, according to its official release notes?

#### Initial broad search

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `whatsnew/3.15.txt` | Release introduction | 0.3017 | Not relevant |
| 2 | `whatsnew/changelog.txt` | Python 3.15.0 final | 0.3142 | Not relevant |
| 3 | `whatsnew/3.14.txt` | Release introduction | 0.3489 | Not relevant |
| 4 | `faq/general.txt` | Version numbering | 0.3575 | Not relevant |
| 5 | `whatsnew/3.13.txt` | Release introduction | 0.3601 | Not relevant |

**Initial assessment:** Failed.

The broad search did not retrieve the two relevant pathlib changes in its top five results.

#### Targeted search 1: Added functionality

**Query:**

`Python 3.15 pathlib Path.mkdir parent_mode parameter intermediate directories`

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `whatsnew/3.15.txt` | pathlib | 0.1306 | Relevant |

**Retrieved information:**

`pathlib.Path.mkdir()` gained a `parent_mode` parameter. It allows specifying the mode for intermediate directories when `parents=True`.

#### Targeted search 2: Removed functionality

**Query:**

`Python 3.15 removed pathlib PurePath is_reserved os.path.isreserved`

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `whatsnew/3.15.txt` | pathlib | 0.2094 | Relevant |
| 2 | `whatsnew/3.13.txt` | pathlib | 0.3236 | Partially relevant |
| 3 | `whatsnew/3.14.txt` | pathlib | 0.3247 | Partially relevant |
| 4 | `library/pathlib.txt` | Comparison to os and os.path | 0.3487 | Partially relevant |
| 5 | `whatsnew/3.14.txt` | os.path | 0.3708 | Not relevant |

**Retrieved information:**

`pathlib.PurePath.is_reserved()` was removed. The release notes recommend `os.path.isreserved()` to detect reserved paths on Windows.

**Final assessment:** Partially successful.

**Notes:**

Both changes were successfully retrieved using targeted queries, but the original broad query failed.

This demonstrates that multi-part questions may require query decomposition and result aggregation instead of relying on a single semantic search.

---

### Q7. Is datetime.datetime.strptime() deprecated in Python, and where can I find its official documentation?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `library/datetime.txt` | date objects | 0.3040 | Not relevant |
| 2 | `library/datetime.txt` | datetime objects | 0.3257 | Partially relevant |
| 3 | `whatsnew/3.15.txt` | datetime | 0.3286 | Relevant |
| 4 | `library/datetime.txt` | Examples | 0.3388 | Partially relevant |
| 5 | `library/datetime.txt` | strftime/strptime format codes | 0.3465 | Relevant |

**Observation:**

The third result contains relevant information about `strptime()` and a deprecation involving date formats containing `%d` without a year.

The result does not establish that the entire `datetime.datetime.strptime()` method is deprecated.

**Final assessment:** Partially successful.

**Notes:**

The answer needs to distinguish between deprecation of a particular format usage and deprecation of the method itself. The official datetime API reference should also be retrieved directly.

---

### Q8. Where can I find the official documentation for json.dumps()?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `tutorial/inputoutput.txt` | Saving structured data with json | 0.3602 | Partially relevant |
| 2 | C API documentation | Code objects | 0.3787 | Not relevant |
| 3 | `whatsnew/2.6.txt` | json module history | 0.3863 | Partially relevant |
| 4 | C API documentation | Code objects | 0.3966 | Not relevant |
| 5 | `faq/programming.txt` | Documentation FAQ | 0.3976 | Not relevant |

**Observation:**

The first result provides a JSON usage example, but the actual `json.dumps()` API reference is not retrieved in the top five.

**Final assessment:** Partially successful.

**Notes:** The search needs stronger exact API matching for `json.dumps()` and should prioritize `library/json.txt`.

---

### Q9. Which modules in the current dataset contain file-handling functions?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | C API documentation | File objects | 0.3486 | Partially relevant |
| 2 | `whatsnew` documentation | Deprecation information | 0.3926 | Not relevant |
| 3 | `library/contents.txt` | Library index | 0.3936 | Partially relevant |
| 4 | `faq/programming.txt` | General FAQ | 0.4028 | Not relevant |
| 5 | `whatsnew/2.1.txt` | New and Improved Modules | 0.4064 | Not relevant |

**Observation:**

The results do not provide a reliable inventory of modules containing file-handling functions.

**Final assessment:** Failed.

**Notes:**

This is a dataset-wide inventory question rather than a normal semantic retrieval question. A structured scan of module documentation and API records would be more appropriate.

---

### Q10. Can I find Python functions related to regular expressions using PyDocsPal?

| Rank | Source | Section | Distance | Assessment |
|---|---|---|---:|---|
| 1 | `howto/regex.txt` | Abstract | 0.3621 | Partially relevant |
| 2 | `library/re.txt` | search() vs. prefixmatch() | 0.3998 | Relevant |
| 3 | `howto/regex.txt` | Regular expression usage | 0.4006 | Relevant |
| 4 | `library/re.txt` | Feedback | 0.4008 | Not relevant |
| 5 | `library/re.txt` | Functions | 0.4240 | Relevant |

**Observation:**

The search identifies the regular expression HOWTO and the `re` module reference. Relevant function documentation appears in the results, including `re.search()` and `re.fullmatch()`.

**Final assessment:** Successful.

**Notes:** The search successfully identifies the relevant module and API documentation, although the introductory passage appears first.

---

## 3. Overall Evaluation

| Assessment | Questions | Count |
|---|---|---:|
| Successful | Q4, Q10 | 2 |
| Partially successful | Q2, Q3, Q6, Q7, Q8 | 5 |
| Failed | Q1, Q5, Q9 | 3 |
| **Total** | **Q1–Q10** | **10** |

### Key observations

1. Relevant documentation is often retrieved, but not always ranked first.
2. Exact API questions need stronger keyword matching.
3. Broad questions involving multiple changes may require multiple search queries.
4. Dataset-wide inventory questions are not well suited to semantic search alone.
5. Retrieval quality depends on chunk boundaries, document metadata, query wording, and ranking.

## 4. Improvements Identified

| Problem | Proposed improvement |
|---|---|
| Exact API names are not ranked highly | Add keyword and exact-match retrieval |
| Relevant passages appear below unrelated results | Combine semantic and lexical rankings |
| Broad questions miss some relevant passages | Implement query decomposition |
| Dataset-wide questions return generic results | Add structured metadata and inventory lookup |
| Repeated or similar chunks appear | Improve deduplication and result aggregation |

## 5. Conclusion

The current PyDocsPal semantic search implementation successfully indexes and retrieves Python documentation chunks using Sentence Transformers and persistent ChromaDB storage.

However, the evaluation shows that semantic search alone is not sufficient for all question types.

The next development step is to implement hybrid search by combining semantic similarity with keyword-based retrieval. This should improve exact API lookups and ranking while preserving the existing vector database.

**Day 7 status:** Semantic search, persistent vector indexing, and initial evaluation completed. Retrieval improvements identified for the next development phase.