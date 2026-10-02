READ the provided Dockerfile.
IDENTIFY build steps and runtime dependencies.
SELECT a slim or distroless base image for the runtime stage.
CREATE a build stage using a full-featured base image.
INSTALL build dependencies in the build stage.
COMPILE the application in the build stage.
EXTRACT the compiled artifacts.
CREATE a runtime stage based on the selected slim or distroless image.
COPY the compiled artifacts into the runtime stage.
EXCLUDE test files, build tools, and other unnecessary files from the runtime stage.
ORDER Dockerfile instructions to maximize layer caching.
GENERATE an explanation for each optimization step.
ESTIMATE the approximate size reduction achieved by the multi-stage build.
OUTPUT the optimized multi-stage Dockerfile and the accompanying explanations.
