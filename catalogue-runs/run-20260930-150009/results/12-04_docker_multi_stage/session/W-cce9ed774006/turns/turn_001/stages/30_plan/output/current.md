READ the original Dockerfile supplied by the user
CREATE a first stage (BUILD) using a suitable build base image and INSTALL build‑time dependencies such as gcc, make, libpq-dev, and any other required packages
COMPILE the application or perform the required build steps within the BUILD stage
CREATE a second stage (FINAL) using a slim or distroless base image
COPY only the compiled artifacts from the BUILD stage into the FINAL stage
EXCLUDE all test files, source code, and build‑time tools from the FINAL stage
REMOVE unnecessary files or package manager caches to reduce layer size
ORDER instructions to maximize Docker layer caching by placing immutable dependency installations early, then copying source files, then running build commands
EXPLAIN each optimization applied, describing why it reduces image size or improves caching
ESTIMATE the size reduction achieved by the optimized multi‑stage image compared to the original Dockerfile image
