READ the provided Dockerfile.
CONVERT the Dockerfile into a multi-stage Dockerfile that minimizes final image size.
USE a slim or distroless base image for the runtime stage.
SEPARATE build dependencies from runtime dependencies.
EXCLUDE test files and build tools from the final image.
LEVERAGE layer caching to reuse unchanged layers.
INCLUDE an explanation for each optimization step.
ESTIMATE the rough size reduction achieved by the multi-stage build.
OUTPUT the optimized Dockerfile and the accompanying explanations.
