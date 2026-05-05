# Critique of the appendix

This document can be viewed as a structured document that serves as code review for the provided [Jupyter Notebook](../docs/assessment/20260428_candidates-tech-assess.ipynb).

It contains two sections with complementary information. Reading both is not required. The first section organizes all the comments by principle ([see this document for more detail](DESIGN_PRINCIPLES.md)), and therefore the section on [identified antipatterns by code line](#identified-antipatterns-from-appendix-jupyter-notebook) can be optionally skipped.

## Organized by principle

### 1. Software Engineering (P1)

- There is no data validation in any of the proposed classes. For example, the `BeliefState` class' methods should at least perform some field-level validations to avoid corrupted or unfeasible data from being saved.
- There is no type hints for all function returns, and where there is, it is not done appropriately (e.g., `BeliefState.get_belief_at_location` returns a Dict, which is ambiguous and not safe according to best OOP practices)
- There is no error handling throughout the notebook
- There is no traceability (logging) anywhere in the notebook
- The Docstring placeholders are not just unnecessary, but writing an actual Docstring is good practice by itself.

(Items: 3, 15, 16, 17, 18)

### 2. Representation (P2)

- The current representation of uncertainty involves "measurement" rows in a Pandas dataframe, where one column represents the S-wave velocity `vs` and other column a so-called `vs_uncertainty`. The latter variable is not just not documented, but it most certainly does not represent uncertainty in reasonable way. A random variable is best represented with a probability distribution type and enough statistical parameters, concepts which are well documented in the literature and more appropriate for this task.
- In the instructions of the assessment is is stated that the value of soil saturation for a given point in space (x,y,z) has uncertainty itself. For the exmple, soil saturation is a numerical parameter and fails to represent this uncertainty. The point above applies for representing this variable instead of with a scalar alone.
- When adding and reading a belief indexed by location, the three values (lat, lon and depth) are encoded as numerical variables (e.g., of type int). This level of granularity in the indexing fails to represent belief in a practical manner. Instead, a discretization (parameterized by deltas in lat, lon and depth) would be more appropriate for practical purposes. Otherwise, the belief for two approximately identical (which differ by a negligible ammount) points in space would be treated as separate.

(Items: 6, 8, 14)

### 3. Update mechanism (P3)

- The `update_belief` function of the notebook does a simple arithmetic average between the new observation and the current belief. This calculation is not appropriate nor done correctly. A still inappropriate but more correct approach would be to take the average with a meaningful denominator (taking into account the exact number of updates the exact variable has undergone), instead of dividing by 2 and giving more weight to the new observations as they arrive. On the other hand, a more appropriate way to update the belief would be to use a poper artifact from probability theory, such as using bayes theorem or more sophisticated methods designed to handle probabilities in light of new evidence.
- Additionally, the `update_belief` is called from `SequentialProcessor.process_batch` with empty `current_belief` (`{}`). This suggests that it is either a bug or unfinished.
- Because Vs and soilsat influence each other, they are correlated. The current code treats their uncertainties as completely independent.

(Items: 10, 13)

### 4. Responsibility and Modularity (P4)

- There is no logical responsibiliy assignment for the different classes defined in the notebook.
- There is a lack of OOP, clean code and other sofwtawre engineering best practices that would help the code become more maintainable and modular. The main thing I would argue this code lacks is the creation of interfaces for BeliefRepresentation and UpdateMechanism that would become the 
"language" in which the rest of the code communicates, separating the infrastructure (actual implementation of both interfaces) with the application (processing of such beliefs) layer. This improves readability and makes the modules swappable.
- The main functions that deal with these kind of objects must contain type hints for good practices and robustness.

(Items: 2, 5, 7, 9, 19)

### 5. Concurrency (P5)

- The singleton pattern implemented with `GlobalBeliefManager` introduces global state (normally bad design choice due to potential issues with debugging, maintainability, concurrency, understandability, etc.). Instead, a pattern like Dependency Injection would unhide the coupling and avoid global state.
- The current singleton pattern forces the lock to be global and disabling the 'disjoint update' feature that is a requirement. Instead, a better approach for concurrency would be so that the locks are owned by a store module instead of a global belief manager, making read and write operations possible for different blocks.

(Items: 1, 12)

### 6. Storage (P6)

- The notebook uses pandas without a justifiable reason to do so. `pd.concat` copies the dataframes, allocating memory and performing column checks, reindexing and copying the whole file for each new measurement added.
- Serialized files (e.g., pickle) or semi-structured files (CSV) may not be the most efficient choice for data storage. Instead, considering Zarr or HDF5 would improve update, and read/write operations for this particular application.

(Items: 4, 11)


## Identified Antipatterns from Appendix (Jupyter Notebook)

1) l.60 -> GlobalManager implements singleton, introducing global state. Also bad for concurrency. (could change for dependency injection?)
2) l.79 -> Type not returned, if BeliefState , it should returne that type. (could use repository pattern)
3) l.21 -> add_measurement has no validation
4) l.26 -> Pandas dataframe concatenation creates a new dataframe, allocates memory, and involves checking columns, reindexing and copying
5) l.131 -> add_measurement should not recieve raw values, instead, a Measurement object that has its own validation when created. 
6) l.24 -> vs and vs_uncertainty are two columns, this does not represent uncertainty accurately. (instead, an object with dist type, mean and variance is needed. This can be an interface that different instances implement[go-style])
7) l.28 -> get belief should return a belief (how ever it is represented) not a dict.
8) l.23 -> soilsat is represented as a scalar. In the instructions it said that this itself has uncertainty
9) l.48 -> current_belief should be a belief (however that is represented (e.g., obj Belief)), not a dict. Also, new_observations should be an object
10) l.50,51 -> The update belief function is a mean, not an actual update
11) l.85 -> storing files is not efficient in this application. -> Pickle requires loading whole objects and CSV requires scanning whole files. (Neither supports random access. For a grid that exceeds RAM and must support concurrent updates on disjoint regions, consider Zarr or HDF5. Each block on disk covers a region of the grid. Updates to different regions touch different files, so they don't contend at the I/O layer. This matches the locking strategy below: the lock unit and the storage unit are the same. This is owned by a BeliefStore, the lock is also owned by it.)
12) l.98 -> sequential update for a huge space can be bad idea, instead we should think if it can be a parellelizable process
13) l.108 -> the line passes empty 'belif' ({}), it would never update
14) l.28 -> this get would require exact matches, and would hardly match. instead, the space should be a discretized grid (with a parameter in config for how), or something else, but not exact field to field matches
15) There is no error handling at all
16) There is no logging at all
17) There is no type safety (however possible in python)
18) There are unsused classes and functions
19) The actual division and selection of classes does not have a logical pattern.