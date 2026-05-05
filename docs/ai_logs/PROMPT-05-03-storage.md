# Implementation Prompt and Task 3.1 LISTENER (Pass 1 of 2)

## Context

Continuing Task 3.1 of Option 3 (Perception + Actuation). LISTENER polls seismic events from two agencies (A primary, B fallback), validates them, deduplicates, and persists to SQLite.

**References -> read before coding:**
- `option3_perception_actuation/DESIGN.md` sections with 3.1 are the source of truth.
- `DEV.md` contains coding conventions and standards.
- Existing files under `option3_perception_actuation/` -> each has a module-level docstring describing its responsibility. Read those docstrings before adding code; they tell you what each file is for and how it fits in.

## Project layout

The `agencies/` package and `listener/{config,models}.py` are already implemented. The remaining files under `listener/` are skeletons and their docstrings define their scope.

## Scope of this session

Implement, per their docstrings:
- `listener/storage.py`
- `listener/agency_client.py`
- Shared logging setup (per DEV.md)
- Unit tests for storage and agency client (happy path, dedup for storage; timeout and retry exhaustion for the client)

## Strict Constraints

From DESIGN.md sections with 3.1:

- `ClientSeismicEvent` Pydantic model is the source of truth for validation from the client side
- SQLite via `sqlite3` stdlib. No ORM. `UNIQUE(eid)` + `INSERT OR IGNORE`.
- Config: YAML -> Pydantic. Fail fast at startup on bad config.
- Dedup by `eid`. Cross-agency `eid` equivalence is out of scope.
- No AI agent frameworks (forbidden by the assessment for Option 3).

## Out of scope for this pass

- `listener/fallback.py` and `listener/listener.py`
- End-to-end test and demo wiring

## Rules

- If a design question comes up that DESIGN.md doesn't answer, stop and ask. Don't invent.
- Match the style of existing code.
- Tests alongside code.