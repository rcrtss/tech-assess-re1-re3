
# Identified Design Principles for the BELIEVE Module

I have identified some basic principles to derive the design of the BELIEVE module from them, and defined them in this document.

This serves as a guide for identifying priorities and actual requirements of the module. The [Appendix code review](./APPENDIX_CRITIQUE.md) and the [Option 2 solution design](../docs/DESIGN.md/#tasks-21-and-22-design-choices) were done and built around these basic principles I defined.

## (P1): Software Engineering Best Practices

Software Engineering best practices (such as data validation, testing, error handling, traceability, type safety, etc.) allow for modularity, scalability, maintainability, and robustness, all of which are enable safe and high-quality software.


## (P2): Uncertainty Representation

A **belief** about a quantity is a probability distribution over that quantity (wich is also known as a random variable). For that same reason, it cannot be accurately represented by a scalar alone.

## (P3): Belief Update

Updating a belief means modifying a probability distribution over random variable after new evidence is observed. This can be done in many ways, but probability theory is widely accepted and provides the means to do exactly this.

## (P4): Responsibility and Modularity

In the context of this problem, where it is specified that components should have a clear responsibility and be easy to swap, additional to the actual representation and update mechanisms, it is just as important to provide patterns that enable this modularity for the system to be future proof. 

## (P5): Concurrency

Updates are expected to be accessed concurrently in disjoint regions. This transforms the concurrency problem into a decision problem of what to lock. For this case, locks should be done in small units of data storage, not on the whole dataset.

## (P6): Memory Efficiency

Such a huge ammount of data requires that its handling is performed only in the relevant chunks, avoiding loading or processing large ammounts of data that should not be relevant for a specific operation.
