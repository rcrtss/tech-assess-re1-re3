# Rsearch Log

This document contains the concept definitions and (maybe) some assumptions considered during the execution of the assessment.

It should be seen as a support file that contains unordered logs of technical concepts and definitions that needed to be researched for a better understanding of the problems.

## Signature of Seismic Events (LISTENER: Task 1.1 and Task 3.1)

{Definition} **Hypocenter**: "A hypocenter or hypocentre, also called ground zero[1][2] or surface zero (...). In seismology, the hypocenter of an earthquake is its point of origin below ground; a synonym is the focus of an earthquake." - [Wikipedia](https://en.wikipedia.org/wiki/Hypocenter)

{Practical Assumption} Measuring units not specified (only stated as 'depth') we assume its measured in Kilometers.

{Definition} **Azimuth**: "is the horizontal angle from a cardinal direction, most commonly north, in a local or observer-centric spherical coordinate system." - [Wikipedia](https://en.wikipedia.org/wiki/Azimuth)

## Velocity Model Wave Propagation

{Definition} **P-Waves**: A P wave (primary wave or pressure wave) is one of the two main types of elastic body waves, called seismic waves in seismology. P waves travel faster than other seismic waves and hence are the first signal from an earthquake to arrive at any affected location or at a seismograph. P waves may be transmitted through gases, liquids, or solids. - [Wikipedia](https://en.wikipedia.org/wiki/P_wave)

{Definition} **S-Waves**: In seismology and other areas involving elastic waves, S waves, secondary waves, or shear waves (sometimes called elastic S waves) are a type of elastic wave and are one of the two main types of elastic body waves, so named because they move through the body of an object, unlike surface waves. - [Wikipedia](https://en.wikipedia.org/wiki/S_wave)

{Definition} **Soil Saturation**: Fraction of pore space in soil/rock that is filled with water (0 = dry, 1 = fully saturated). Relevant to wave propagation because saturation strongly increases P-wave velocity (water is incompressible relative to air). - [Wikipedia](https://en.wikipedia.org/wiki/Water_content)

{Definition} **Velocity Model**: Spatial map of seismic wave speeds (typically Vp and Vs) through the subsurface. Can be 1D (layered, depth-only), 2D (vertical cross-section), or 3D. Used to compute travel times, locate hypocenters via inversion, and forward-simulate wavefields. - [Wikipedia](https://en.wikipedia.org/wiki/Seismic_tomography)

## In-memory Storage for Large Data

{tool} **Zarr**: Open format and Python library for chunked, compressed, N-dimensional arrays. Each chunk is stored as an independent object/file, enabling parallel reads, partial slicing, and cloud-native access (S3, GCS) without loading the full array. Common in geosciences (Pangeo stack) and ML data pipelines. - [zarr.dev](https://zarr.dev/)

{tool} **HDF5**: Hierarchical Data Format v5. Single-file binary container for large heterogeneous scientific datasets, with a filesystem-like internal structure (groups → datasets), chunking, compression, and rich metadata. Standard in HPC and scientific computing; less cloud-friendly than Zarr because all chunks live inside one monolithic file (concurrent writes are constrained). - [HDF Group](https://www.hdfgroup.org/solutions/hdf5/)
