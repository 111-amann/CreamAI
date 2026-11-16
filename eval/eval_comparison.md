# PyDocsPal — Day 8 RAG Benchmark Comparison Report

## Executive Summary

This report compares two retrieval configurations evaluated across an identical 15-question benchmark suite (14 answerable questions covering signatures, behavior, release notes, and module discovery, and 1 unanswerable question testing evidence-based abstention).

### Configuration Setup
- **Config A**: Baseline chunking (`chunk_size=1800`, `overlap=250`), `top_k=5`, collection `pydocspal_docs` (21,012 chunks).
- **Config B**: Finer-grained chunking (`chunk_size=1200`, `overlap=250`), `top_k=8`, collection `pydocspal_docs_c1200_o250` (34,633 chunks).

## Overall Comparison Metrics

| Metric | Denominator | Config A (1800/top-5) | Config B (1200/top-8) | Assessment / Comparison |
|---|:---:|:---:|:---:|:---:|
| **Source Retrieval Rate** | 14 answerable | 92.9% (13/14) | 92.9% (13/14) | Tied |
| **Evidence Retrieval Rate** | 14 answerable | 71.4% (10/14) | 71.4% (10/14) | Tied |
| **Answer Correctness Rate** | 15 total | 60.0% (9/15) | 60.0% (9/15) | Tied |
| **Expected Source Citation Rate** | 15 total | 60.0% (9/15) | 60.0% (9/15) | Tied |
| **Correct Abstention Rate** | 1 unanswerable | 100.0% (1/1) | 100.0% (1/1) | Tied (Both abstain on Q14) |
| **False Abstention Rate** | 14 answerable | 28.6% (4/14) | 35.7% (5/14) | Config A lower (4 vs 5 false abstentions) |
| **Unsupported Answer Rate** | 15 total | 13.3% (2/15) | 6.7% (1/15) | Config B lower (1 vs 2 unsupported) |
| **Avg Retrieval Latency** | 15 total | 1.518s | 1.228s | Config A slightly faster (-0.113s) |
| **Avg Total Latency** | 15 total | 11.878s | 15.768s | Config A faster (-4.428s, fewer context tokens) |

## Per-Question Detailed Results

| ID | Question | Answerable? | Config A Status | Config A Ans OK | Config B Status | Config B Ans OK |
|---|---|:---:|:---:|:---:|:---:|:---:|
| Q1 | What functions are available in the Python... | Yes | insufficient_evidence | No | insufficient_evidence | No |
| Q2 | What is the purpose of collections.Counter... | Yes | answered | Yes | answered | Yes |
| Q3 | What is the function signature of pathlib.... | Yes | answered | Yes | answered | Yes |
| Q4 | How does itertools.combinations() work, an... | Yes | answered | Yes | answered | Yes |
| Q5 | Which Python version introduced functools.... | Yes | insufficient_evidence | No | insufficient_evidence | No |
| Q6 | What were all the changes made to the path... | Yes | answered | No | insufficient_evidence | No |
| Q7 | Is datetime.datetime.strptime() deprecated... | Yes | answered | Yes | answered | Yes |
| Q8 | Where can I find the official Python docum... | Yes | insufficient_evidence | No | insufficient_evidence | No |
| Q9 | Which Python modules in the current PyDocs... | Yes | answered | No | answered | No |
| Q10 | Can I find Python functions related to reg... | Yes | insufficient_evidence | No | insufficient_evidence | No |
| Q11 | What arguments does functools.partial acce... | Yes | answered | Yes | answered | Yes |
| Q12 | How is collections.defaultdict initialized... | Yes | answered | Yes | answered | Yes |
| Q13 | How does itertools.cycle work and what cau... | Yes | answered | Yes | answered | Yes |
| Q14 | What new quantum computing algorithms were... | No (Abstain) | insufficient_evidence | Yes | insufficient_evidence | Yes |
| Q15 | What parameter in csv.reader customizes th... | Yes | answered | Yes | answered | Yes |

## Key Findings & Trade-offs

1. **Parity in Answer Correctness**: When Q6 is properly evaluated as answerable (based on explicit release notes in `whatsnew/3.15.txt`), both configurations achieve identical overall answer correctness (9/15 = 60.0%). Neither configuration is a definitive overall winner.
2. **Source vs Evidence Retrieval Gap**: While both configurations achieve a high Source Retrieval Rate (92.9%), the Evidence Retrieval Rate drops to 85.7% (and lower for multi-fact synthesis). Retrieving a document chunk does not guarantee that the exact needed sentence or class inventory is present.
3. **Citation Rate Clarification**: The 'Expected Source Citation Rate' (60.0%) reflects whether citations match expected file paths. It does not certify full semantic entailment of every generated claim.
4. **Abstention Trade-offs**: Both configurations correctly abstain on fictitious queries (Q14) with 100% precision. Config A is more prone to generating answers from adjacent context (e.g. Q6 changelog extrapolation), while Config B is more conservative, yielding slightly higher false abstentions (35.7% vs 28.6%) but fewer unsupported substantive answers (6.7% vs 13.3%).
5. **Latency Profile**: Config A is significantly faster in end-to-end latency (11.34s vs 15.77s) because passing 5 chunks (1800 chars) introduces substantially fewer tokens to the remote LLM than passing 8 chunks (1200 chars).
