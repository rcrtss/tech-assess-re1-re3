# Design File

This document outlines the decisions and its justifications for the solutions' designs.

## Excercise Selection

Options 2 (Belief State) and 3 (Reasoning & Actuation) were selected.

This combination:
- Involves design judgment
- Involves systems engineering
- Covers four of the agent's functional modules (PERCEPTION, BELIEF, RAP, and ACTUATION)
- Best aligns with personal interests and past experience

## Option 3

### Task 3.1

#### Requirements Summary 3.1

#### Assumptions 3.1

**Event Timestamp**: It may be unreasonable to think that a specific event's timestamp is always consistent between agency A and B, and thus we assume it is not always the case. For that reason, only when switching from one agency to another, to avoid duplicating data in the moment of switching (and only in that case), the data is compared not only by event timestamp but also by using other metadata (e.g., latitude, longitude, magnitude, etc.). In the rest of the cases (stop or restart), we can avoid duplication by simply comparing the event's UTC timestamp `timestamp`.

#### Architecture Decisions 3.1

#### Technical Debt / Future Work 3.1
