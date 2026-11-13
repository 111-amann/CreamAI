# PyDocsPal – Prompt Comparison Evaluation

## Objective

Compare two prompt versions to understand how prompt instructions affect the quality, accuracy, and usefulness of PyDocsPal responses.

## Prompt Versions

### Version A – Basic Prompt

- Answers the user's Python question.
- Uses the available documentation context.
- Provides a simple explanation.
- Returns a structured JSON response.

### Version B – Documentation-Grounded Prompt

- Uses retrieved documentation as the primary source.
- Avoids inventing function signatures or version information.
- Explicitly identifies insufficient documentation.
- Separates supported facts from general explanations.
- Provides a confidence score and follow-up question.
- Returns valid JSON.

## Evaluation Questions

The same 10 questions from `docs/user_questions.md` will be used for both prompt versions.

| ID | Question | Evaluation focus |
|---|---|---|
| Q1 | What functions are available in the Python collections module? | Completeness |
| Q2 | What is the purpose of collections.Counter, and how is it used? | Explanation |
| Q3 | What is the function signature of pathlib.Path.read_text()? | Signature accuracy |
| Q4 | How does itertools.combinations() work, and what arguments does it accept? | Explanation and accuracy |
| Q5 | Which Python version introduced functools.cache, and how does it differ from functools.lru_cache? | Version accuracy |
| Q6 | What were all the changes made to the pathlib module in Python 3.15, according to its official release notes? | Handling missing context |
| Q7 | Is datetime.datetime.strptime() deprecated in Python, and where can I find its official documentation? | Deprecation accuracy |
| Q8 | Where can I find the official Python documentation for json.dumps()? | Documentation references |
| Q9 | Which Python modules in the current PyDocsPal dataset contain file-handling functions? | Dataset retrieval |
| Q10 | Can I find Python functions related to regular expressions using PyDocsPal? | Search relevance |

## Evaluation Criteria

Each prompt version will be evaluated using:

1. **Accuracy:** Is the answer factually correct?
2. **Relevance:** Does it answer the actual question?
3. **Grounding:** Does it use the supplied documentation?
4. **Completeness:** Does it include the important details?
5. **Limitation handling:** Does it admit when information is unavailable?
6. **JSON validity:** Does it return the required response structure?

## Results Comparison

Complete this table after running the same questions against both prompt versions.

| Question | Version A | Version B | Better Version |
|---|---|---|---|
| Q1 | Pending | Pending | Pending |
| Q2 | Pending | Pending | Pending |
| Q3 | Pending | Pending | Pending |
| Q4 | Pending | Pending | Pending |
| Q5 | Pending | Pending | Pending |
| Q6 | Pending | Pending | Pending |
| Q7 | Pending | Pending | Pending |
| Q8 | Pending | Pending | Pending |
| Q9 | Pending | Pending | Pending |
| Q10 | Pending | Pending | Pending |

## Observations

To be completed after testing:

- Which prompt produced more accurate answers?
- Which prompt handled missing documentation better?
- Which prompt followed the required JSON format more consistently?
- Did either prompt generate unsupported information?
- Which prompt should be used as the default for PyDocsPal?

## Conclusion

The comparison will help identify which prompt provides more reliable, relevant, and documentation-grounded responses.

The final conclusion will be based on actual test results rather than assumptions.