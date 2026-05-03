```md
# Code Conventions and Standards

This file describes the conventions used for consistency and good practices in this repo (serves for personal organization as well).

## Commit Messages

- Each commit starts with a keyword from the set: [setup, docs, tests, feat, other].
- After such keyword, inside parenthesis, optionally write a tag to link the commit to a high level topic or feature.

Example commit message:

```text
feat (task 3.1): Add domain related concepts to RESEARCH_LOG.md
```

## Coding Principles

- Adhere to SOLID principles
- Keep it simple

## Python Naming

### Directories and Packages

- `snake_case`, lowercase, no hyphens.

### Files

- `snake_case.py`. one clear concept per file.
- Avoid dumping-ground names like `utils.py` or `helpers.py`.

### Classes
- `PascalCase`. nouns.

### Functions and Methods

- `snake_case`. verbs or verb phrases.
- Boolean returns prefixed with `is_`, `has_`, or `should_`.

### Variables

- `snake_case`. self-descriptive to avoid comments.
- Single letters only for short loops or math.
- Plurals for collections, singular for items.

### Constants

- `UPPER_SNAKE_CASE`, defined on top of files.

### Private / Internal

- Single leading underscore (`_name`) signals "don't import from outside".

### Type Hints

- Annotate public function signatures and non-trivial variables.

### Tests

- Test files must start with `test_` for pytest discovery.

### Data Fields (Payloads, DTOs, etc.)

- Keep domain abbreviations from the brief (`eid`, `Mw`, `lat`, `vs`, `soilsat`) at data boundaries, expand inside business logic if clearer.

## Documentation and Comments

- Docstrings should be minimal
- Avoid nouns (tech dependency), hardcoded values and variable names in all docstrings or comments, all namings should be codes unless necessary for readability
- Only comment when code is not self-explainatory or can be amiguous or difficult to understand
- Comments should not be inline, instead above the commented code
