READ the provided Dockerfile
CREATE a multi-stage build with a build stage and a runtime stage
SELECT a slim or distroless base image for the runtime stage
COPY only the compiled artefacts from the build stage to the runtime stage, EXCLUDING test files and build tools
ARRANGE Dockerfile instructions to maximize layer caching (e.g., place infrequently changing commands early)
GENERATE the final image using the optimized multi-stage Dockerfile
DOCUMENT each optimization applied in the Dockerfile
ESTIMATE the size reduction achieved by comparing the final image size to the original unoptimized image
