# Task instruction:

## Phase 1

Refactor the provided Python codebase to support robust swappability between different belief representation and update mechanisms.

### Current Problems and Architectural Flaws:

Restrictive Interfaces: The BeliefRepresentation protocol forces mean() and variance() to return a float. This completely blocks multivariate models (like a Kalman filter), which require state vectors and covariance matrices. Go instead for returning np.arrays as convention in this and similar cases (if any).

Dependency Inversion Violation: BeliefStore is tightly coupled to the concrete GaussianBelief class in its type hints and internal dictionaries, rather than relying on the BeliefRepresentation protocol.

Lack of Type-Safe Bindings: The UpdateMechanism protocol and concrete updaters lack generic type bindings. There is no structural guarantee preventing a 1D Gaussian updater from accidentally accepting a multivariate belief.

Rigid Data Models: VsMeasurement strictly mandates the vs field. A multivariate system must be able to process partial measurements (e.g., observing only soilsat without vs, or vice versa).

Concurrency & Memory Bugs: The locking mechanism in BeliefStore.put_belief contains a critical check-then-act race condition during lock initialization. Furthermore, allocating a permanent lock for every new grid cell creates a severe memory leak as the grid grows.

### Required Actions:

1. Refactor the boilerplate interfaces, models, and BeliefStore to resolve all the problems listed above, ensuring true architectural swappability.
2. Adapt the existing 1D approach (PrecisionWeightedGaussianUpdate and its belief representation) to fully comply with the newly refactored boilerplate.

> Read the Q&A section of this document for context before implmenting any code

## Second Phase

3. Implement a new Kalman Filter approach (a concrete Kalman updater and a concrete multivariate belief representation, see the next section) that successfully implements the refactored boilerplate.

### Guide on Kalman Filter approach for the S-wave velocity and soil saturation problem

1. Use Log-Space for the State Vector: To enforce the physical constraint that S-wave velocity (vs) must be positive and follow a log-normal distribution, track the natural logarithm of the velocity. Your state vector ($\mu$) will be a 2x1 NumPy array representing [soilsat, log(vs)].
2. Encode Dependency in the Covariance Matrix: Initialize a 2x2 covariance matrix ($\Sigma$). The diagonal elements represent the individual uncertainties of soilsat and log(vs). Crucially, set a positive off-diagonal value (covariance) to mathematically bake in the geological rule that velocity increases as soil saturation increases.
3. Implement the Concrete Belief Class: Create a KalmanBelief class that implements the new BeliefRepresentation protocol. Its mean() method must return the 2x1 state vector, and its variance() method must return the 2x2 covariance matrix as np.ndarray types.
4. Dynamically Construct the Observation Matrix ($H$): Because a sensor might measure both variables, or just soilsat, or just vs, your KalmanUpdater must dynamically build the Observation Matrix ($H$). If measuring only soilsat, $H$ is [1, 0]. If measuring both, $H$ is the identity matrix [[1, 0], [0, 1]].
5. Execute the Matrix Update Equations: Inside the apply() method of your KalmanUpdater, use NumPy to execute the standard equations. Calculate the Kalman Gain ($K$), use it to pull the prior mean toward the measurement (mu_new = mu + K @ (z - H @ mu)), and shrink the covariance matrix (Sigma_new = (I - K @ H) @ Sigma).
6. Provide a Physical State Extractor: Because the system tracks $log(vs)$, the actual downstream Agentic system will need real physical numbers. Add a helper method to safely transform the internal state back to real values using the log-normal mean formula: true_vs = exp(mu_log_vs + (variance_log_vs / 2)).

## Q&A

Q: For partial measurements in VsMeasurement, how should measurement noise be structured for the Kalman updater?
A: I recommend encapsulating the value and its uncertainty into a single, reusable Pydantic model (e.g., UncertainValue), and making them optional fields on the measurement payload. By defining a simple sub-model, you guarantee that a value never exists without its corresponding noise: