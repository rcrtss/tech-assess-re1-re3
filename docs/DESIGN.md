# Design File

This document outlines the decisions and its justifications for the solutions' designs.

## Excercise Selection

Options 2 (Belief State) and 3 (Reasoning & Actuation) were selected.

This combination:
- Involves design judgment
- Involves systems engineering
- Covers four of the agent's functional modules (PERCEPTION, BELIEF, RAP, and ACTUATION)
- Best aligns with personal interests and past experience

## Option 3. Simple Reasoning and Actuation

![Option 3. Simplified Diagram](../docs/diagrams/tasks_3_1_and_3_2.excalidraw.svg)

### Task 3.1. LISTENER: Event Ingestion Module

#### Explicit Requirements Summary 3.1

- Create LISTENER
  - that pulls real time basic seismic data each 'm' minutes (where m is a **positive integer**)
  - that knows and adheres to the signature of seismic events
  - that has automatic fallback and recovery logic when Agency A becomes unavailable
  - that checks type and validity of downloaded data and logs any anomalies
  - if stopped or reinitiated, or switching agencies, does not pull again data already downloded (avoid duplications) -> suggestion is to consider that downloaded timestamp does not mean different event
- Create Simulated APIs (Agency A and Agency B)
  - that makes new data available as new events occur
  - where the timeline of past events (history) is immutable

#### Design 3.1

In this section we move from what is given in the problem to the actual design decisions. Section [architecture](#architecture-decisions-31) contains the actual design decisions, while sections [assumptions](#assumptions-31), [inputs](#identified-inputs-31),  [outputs](#identified-outputs-31), and [failure modes](#failure-modes-31) contain supporting information for those decisions.  

##### Assumptions 3.1

**Event Timestamp**: It may be unreasonable to think that a specific event ID is shared between agency A and B, and thus we assume it is not necessarily the case. We treat that case (e.i., when switching between agencies) as out of scope. This is noted as external limitation.

**Agency API Endpoints**: These are not given, but we assume that it is reasonable for such a service to expose at least the following endpoints:
- `get_recent_events`: to get the events from a given timewindow -> returns JSON payload with a list of objects of type seismic event
- `get_event_by_eid` to get an event by its event ID (`eid`) -> returns JSON payload with seismic event signature/schema

##### Identified Inputs 3.1

1. Configuration (startup):
   - value of 'm'
   - external services (API) list (id + url)
   - (optional, operative) timeouts, max retries, etc. 
2. Triggers (runtime) 
   - Internal timer to fire polling
   - External endpoint to "pull now" (for Task 2) -> should be independent from internal timer and not break it

##### Identified Outputs 3.1

1. Persisted (database) validated and deduplicated data from events
2. Logs to trace annomalies and debug

##### Failure Modes 3.1

**Startup**
- missing dependencies and similar errors -> mitigated by following instalation and running from README, using good practices (e.g., requirements.txt)
- wrong configuration (levels: structure and values)
  - config fields match expected schema
  - 'm' is positive integer
  - JSON schema (seismic event signature) path is reachable and parsable
- storage path unreachable (e.g., SQLite cannot be opened) -> fail fast at startup with a clear error.

**Communication with APIs (agencies)**
- agency A API Unavailable -> mitigated with fallback and recovery logic (periodic health checks to know when to switch back)
- both Agency A and B APIs unavailable -> LISTENER should stay alive and retry. Somehow inform status as `unhealthy`. Pull now button from orchestrator should return detailed error and avoid hanging.
- single request timeout per agency call -> log error and try for `max_retries`. Trigger protocols explained in previous two points. 
- agencies taking too long to respond -> if no successful pull from any agency has happened in N minutes, the system is no longer in a healthy state.

**Data Validation**
- incomming data does not adhere to seismic event signature -> record rejected in persistance, log anomaly, continue.
- same event from different agencies recorded since we cannot guarantee `eid` equivalence -> OUT OF SCOPE

**Storage and State**
- DB write failure -> log warning and retry, log anomaly (error) if still failing
- restart or stop while pulling and event not persisted -> tag event ID as not persisted. when startup, fetch that list to ask service by ID

**Asynchronicity and Concurrency**
- LISTENER serves two trigger sources: an internal timer (every `m` minutes) and a "pull now" endpoint callable by the orchestrator on behalf of multiple tenants. Concurrent triggers risk redundant agency calls and duplicate inserts. -> mitigated by short-circuit when pull in progress AND idempotency (e.g., `INSERT OR IGNORE ON eid`)

##### Architecture Decisions 3.1

**Configuration**
- [x] Configurable to what extent? -> As simple as possible. Pydantic validation. YAML for configuration for readability.

**Logging**
- [x] How to log? -> Shared log system for consistency, log writing practices documented in DEVS.md to avoid "over-logging" and keep consistency.

**Data Validation**
- [x] Pydantic vs JSON schema for data validation (when respond recieved from agencies)? -> The seismic event contract is defined as a Pydantic model (SeismicEvent), which serves as the single source of truth for validation, type-safe domain objects.

**Persistance**
- [x] Use ORM or not? -> avoid using it. it could help for future portability, but we loose siplicity. notes as technical debt.
- [x] Which database to use? -> SQLite, since we start simple, we stick with light tool that runs locally and has low setup cost

**Host Agency Services**
- [x] How and where to host Agency services? -> standalone with FastAPI running on separate ports (8001 and 8002), reachable through REST locally.

**Agency Switching**
- [x] What are the rules for switching?
  - if agency A unavailable, switch to Agency B
  - periodically send checks to Agency A to test availability
  - when A available again, recover

**Agency API**
- [x] What enpoints could it potentially have?
  - `get_recent_events`: to get a list of events in a timewindow (e.g. `?since=<timestamp>`) -> returns JSON payload with list of objects of type seismic event
  - `get_health_status`: to query for availability
  - (Optional, and will not do for now until it is clearly needed) `get_event_by_eid` to get an event by its event ID (`eid`) -> returns JSON payload with seismic event signature/schema
- [x] How to ask for the data from LISTENER? -> each pull queries a fixed lookback window wider than m, overlap is harmless thanks to dedup.

**Deduplication**
- [x] How to avoid duplicationm? -> Use `eid` to differentiate events and avoid duplication.

**Mitigate Concurrency Risks**
- [x] How to deal with asynchronicity and deduplication from multi-tenant calling orchestration at same time? -> asyncio.Lock for short-circuit, SQLite UNIQUE constraint on eid with INSERT OR IGNORE for persistence-level idempotency.

#### Tests 3.1

**Polling**
- [] external triggering should NOT break internal timer fire polling

TODO:day3: finish test cases list

#### Technical Debt / Future Work 3.1

- health check of service (e.g., heartbeat) -> not core functionality, always a good practice for service orchestration but out of scope
- event-driven notification system for anomalies (complementary to logs) -> would be a good feature but are out of scope
- use of sqlite3 and not using an ORM creates a potential risk for future migration and refactoring, but we accept this to gain simplicity for this assessment
