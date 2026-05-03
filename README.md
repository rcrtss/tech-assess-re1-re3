# Technical Assessment — AI Agent Development

**Candidate**: Rodrigo Cortés

**For Positions**: AI Software Research Engineer (RE1~RE3)

<!-- TODO:day6: all sections should be filled and polished -->

## TL;DR

## Install

1. Create and activate a new virtual environment (Python 3.10.12 was used for this implementation. This is the recommended version.)

Example:
```sh
pyenv virtualenv 3.10.12 bsc-tech-assessment
pyenv activate bsc-tech-assessment
```

2. Install the dependencies from `requirements.txt`:

```sh
pip install -r requirements.txt
```

## Run

### Task 3.1

To run the demo of task 3.1:

**Terminal 1:**
```sh
make demo_task_3_1
```

**Terminal 2:**
```sh
# Check listener health
curl http://127.0.0.1:8000/health

# Trigger pull manually (no orchestrator needed)
curl -X POST http://127.0.0.1:8000/pull_now

# Stop Agency A to trigger fallback
make stop_agency_a

# Restart Agency A to trigger recovery
make start_agency_a

# Control Agency B independently
make stop_agency_b
make start_agency_b
```

## Design Decisions

## Tools and Technologies

## Run Tests

To run all tests execute:

```sh
make test_all
```

To run tests for a specific task, follow this format:

```sh
make test_task_3_1
```

## AI Usage

AI tools (i.e., Large Language Models) were used for two main purposes:

- General understanding of the tasks
- Coding assistance

For general understanding of tasks, Claude Sonnet 4.5 was used in the web UI.

For all coding assistance activities using AI, the conversations were recorded and are located in the `docs/ai_logs` directory, together with some larger prompts saved as `markdown` files.

For coding, the main Large Language Models used were the following:

- Claude Haiku 4.5 (via VSCode Copilot) -> main coding assistant for listener implementation
- Claude Sonnet 4.6 (via VSCode Copilot) -> secondary coding assistant for listener implementation
- GPT-5.4 (via VSCode Copilot) -> used for debugging, mainly during demo setup for listener