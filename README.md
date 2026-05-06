# Technical Assessment — AI Agent Development

**Candidate**: Rodrigo Cortés

**For Positions**: AI Software Research Engineer (RE1~RE3)

## TL;DR

My response to the assessment partially answers Option 2 and Option 3 of the assessment, and is divided in the following parts:

**Option 2: Belief State**
- [Design for task 1 and 2](./docs/DESIGN.md/#option-2-belief-state-conceptual-design-and-implementation-choices)
- [Code review of Appendix A](./option2_belief/APPENDIX_CRITIQUE.md)
- [Alternative implementation (toy example)](./option2_belief/alternative_implementation.ipynb)

**Option 3: Simple reasoning and actuation (task 1 only)**
- [Design for task 1](./docs/DESIGN.md/#option-3-simple-reasoning-and-actuation)
- [Runnable Demo for task 1](#run)
- [Comments on how I would handle task 2](./docs/DESIGN.md/#task-32-multi-tenant-pipeline-for-reasoning-and-actuation)

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

### (Opt. 2) BELIEF Module: Tasks 1 and 2

Please refer to [Design for task 1 and 2](./docs/DESIGN.md/#option-2-belief-state-conceptual-design-and-implementation-choices).

### (Opt. 3) REASON and ACTION Module: Task 1 only

#### Config Setup

You will need to have a valid `.option3_perception_actuation/listener/config.yaml` file for the demo to run correctly. To avoid pushing to the Github repository configuration files, I only left a `config.example.yaml` to show the config skelleton, but the values must be edited.

The suggested steps:

1. Copy the `config.example.yaml` and rename it. From root:

```sh
cd option3_perception_actuation/listener
cp config.example.yaml config.yaml      
```

2. Replace the fields or the whole file with the  contents of the following yaml block:

```yaml
listener:
  pull_now_endpoint:
    host: "127.0.0.1"
    port: 8000

  # DEMO CONFIG: Values are interpreted as SECONDS (not minutes) for rapid demo execution.
  # In production, these would be in minutes: poll_interval_minutes: 1, lookback_window_minutes: 5, etc.
  # For demo purposes, interpreted as seconds to show fallback/recovery quickly:
  poll_interval_minutes: 5          # Interpreted as 5 seconds (production: 1 minute)
  lookback_window_minutes: 30       # Interpreted as 30 seconds (production: 5 minutes; must exceed poll_interval)
  liveness_threshold_minutes: 10

  timeout_seconds: 5
  max_retries: 3
  health_probe_interval_seconds: 3

  storage_path: "./data/listener.db"

  primary_service:
    name: "Agency A"
    url: "http://127.0.0.1:8001"

  secondary_service:
    name: "Agency B"
    url: "http://127.0.0.1:8002"
```

#### To run the demo of task 3.1:

cd to root directory of the project

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

All design choices are located in the dedicated file [DESIGN.md](./docs/DESIGN.md). Please refer to it for information on the design of each part of the solution.

## Tools and Technologies

- Development done in Windows 11 with WSL2 (Ubuntu 22.04)
- Makefile + shell script for running Task 3.1 demo
- curl 7.81.0 for interacting with Task 3.1 demo
- yaml files for configuration (Task 3.1)
- Python 3.10.12
- Pyenv for version management
- See `requirements.txt` for all libraries installed during development (I cannot guarantee that all of them are actually used, but I did start with a clean pyenv)
- `pip` for library installation

### General/Support tools

- VSCode Copilot (AI for coding assistance): [see this section](#ai-usage)

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
- Gemini 3.1 Pro for meta-prompting (asking to create clean prompts)