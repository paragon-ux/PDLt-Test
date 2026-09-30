READ the original Dockerfile supplied by the user
CONVERT the Dockerfile into a multi‑stage Dockerfile separating build‑time dependencies from runtime dependencies
SELECT a minimal base image (e.g., alpine‑slim or distroless) for the final stage
EXCLUDE test files, build tools, and any intermediate artifacts from the final image
STRUCTURE the stages to maximize layer caching for incremental builds
EXPLAIN each optimization step, including why each dependency is moved to a build stage, why the chosen base reduces size, and how layer ordering improves cache reuse
PROVIDE an estimate of the size reduction of the final image compared to the original image, expressed as an approximate megabyte difference or percentage
RETURN the complete optimized multi‑stage Dockerfile and the accompanying explanation
