# Implementation Prompt: Task 3.1 LISTENER (Pass 2 of 2)

## Context

Continuing Task 3.1 of Option 3. Pass 1 delivered logging, storage, agency client, and their unit tests. This pass wires them into a working LISTENER and demo.

**References: read before coding:**
- `option3_perception_actuation/DESIGN.md` sections 3.1 are the source of truth (maily Architecture Decisions 3.1 and Failure Modes 3.1).
- `DEV.md`: coding and logging conventions and standards.
- Already finnished Pass 1 instructions and code (PROMPT-05-03-storage) and the existing modules under `option3_perception_actuation/`: each file has a module-level docstring describing its responsibility. Read those docstrings before adding code.

## Scope of this pass

Implement, per their docstrings:
- `listener/fallback.py`
- `listener/listener.py`
- Unit tests for fallback logic (switch, recover, both-down)
- End-to-end test against the real agency FastAPI servers (pull, dedup across simulated restart, A→B→A fallback)
- Demo wiring per DESIGN.md "Demo Design": single Makefile entry point that spins agencies + listener with logs visible; separate Makefile targets to stop/start each agency independently so fallback and recovery can be triggered live during the demo.

## Strict Constraints

From DESIGN.md sections with 3.1:

- `asyncio.Lock` to prevent overlapping pulls when timer + "pull now" fire together.
- Each pull queries a lookback window wider than `m`. Overlap is harmless because of dedup.
- A is primary; on unavailability switch to B; periodically check A; recover when A returns.
- Cross-agency `eid` equivalence is out of scope.
- No AI agent frameworks (forbidden by the assessment for Option 3).

## Deliverable

`make demo_task_3_1` that:
1. Starts Agency A, Agency B, and the LISTENER.
2. Listener polls, validates, persists to SQLite.
3. Killing Agency A triggers fallback to B (visible in logs).
4. Restoring Agency A triggers recovery (visible in logs).
5. Stopping and restarting the listener does not produce duplicates.
6. `make test_task_3_1` passes, including the end-to-end test.
7. Separate Makefile targets exist to stop and start Agency A and Agency B independently, so steps 3 and 4 can be triggered manually during the demo.

## Out of scope for this pass

- Orchestrator / external "pull now" caller integration (Task 3.2). Expose the hook on the listener; don't wire the orchestrator.
- Cross-agency `eid` equivalence.

## Rules

- If a design question comes up that DESIGN.md doesn't answer, stop and ask. Don't invent.
- Match the style of existing code.
- Tests alongside code.