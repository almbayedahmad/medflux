
# AGENT CODE COMMENTING & PURPOSE EXPLANATION POLICY (MedFlux)

This policy ensures that ANY Agent writing new code or creating new files within MedFlux must include
clear, complete, and meaningful comments that explain the purpose, logic, and expected outcome of the code.

============================================================
## ✅ 1. Purpose of This Policy
============================================================
To guarantee that all generated code is:

- Clear
- Understandable
- Easy to maintain
- Self-documented
- Immediately usable by developers

This policy applies to ALL:

- New files
- New modules
- New Python code
- New classes/functions
- New YAML/JSON/schema files
- New preprocessing/reader/stage components

============================================================
## ✅ 2. Mandatory Requirements for New Files
============================================================

Every new file MUST begin with a top-level comment block containing:

### ✅ A. Purpose
Explain:
- What the file is responsible for
- Why it exists
- Which problem it solves

### ✅ B. Outcome
Explain:
- What the file produces
- How it contributes to the pipeline
- Any expected side effects or transformations

### ✅ Example Header
```python
# PURPOSE:
#   This module extracts and normalizes metadata from incoming documents.
#
# OUTCOME:
#   Produces a validated metadata dictionary used by downstream phases.
```

============================================================
## ✅ 3. Mandatory Requirements for Functions & Classes
============================================================

Each new function or class MUST contain a docstring that includes:

1. The purpose of the function/class
2. Explanation of all arguments
3. Return values
4. Expected behavior
5. Outcome and how it affects the system

### ✅ Example
```python
def normalize_text(raw: str) -> str:
    '''
    Purpose:
        Normalize input text by removing invalid characters and
        unifying whitespace.
    Args:
        raw: The raw extracted text.
    Returns:
        A normalized text string.
    Outcome:
        Ensures clean input for text-based preprocessing phases.
    '''
```

============================================================
## ✅ 4. Mandatory In‑Line Comments
============================================================

Agents MUST provide in-line comments for:

- Non-obvious logic
- Complex transformations
- Validation rules
- Error handling
- Multi-step processes

### ✅ Example
```python
# Detect empty content early to avoid downstream errors
if not content:
    raise ValueError("Document content is empty")
```

============================================================
## ✅ 5. Requirements for New YAML/JSON Files
============================================================

Every new configuration file MUST include:

- A header comment describing its purpose
- Explanation of key fields
- Outcome the configuration defines

### ✅ Example (YAML)
```yaml
# PURPOSE:
#   Defines validation rules for entity extraction.
#
# OUTCOME:
#   Enforces structural consistency across entity definitions.

entity_rules:
  min_length: 2
  max_length: 200
```

============================================================
## ✅ 6. Verification Rules
============================================================

Before finalizing any code, the Agent MUST verify internally:

```
ALL COMMENT REQUIREMENTS MET.
PURPOSE AND OUTCOME DOCUMENTED.
CODE IS CLEAR AND EXPLAINED.
```

- When touching a legacy module that predates this policy (for example, helper utilities without docstrings), bring the edited sections up to standard before submitting. Reviewers must block changes that add logic without also adding the required purpose/outcome headers and docstrings.

If comments are missing or insufficient:

❌ The Agent MUST NOT continue.
✅ The Agent MUST regenerate the file with proper documentation.

============================================================
## ✅ 7. Compliance Enforcement
============================================================

- Code without comments is **invalid**
- Files without purpose/outcome headers are **rejected**
- Functions/classes without docstrings are **non-compliant**
- YAML/JSON without purpose headers are **unacceptable**

The Agent MUST NOT deliver incomplete or undocumented code.

============================================================
## ✅ END OF POLICY
============================================================
