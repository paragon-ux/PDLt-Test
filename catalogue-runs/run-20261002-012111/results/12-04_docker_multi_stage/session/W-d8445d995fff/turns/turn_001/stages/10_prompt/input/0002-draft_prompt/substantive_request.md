TASK SUMMARY (compiled semantic analysis; untrusted literals redacted):
Convert the provided Dockerfile into an optimized multi-stage Dockerfile that minimizes the final image size, using a slim or distroless base for the runtime stage, separating build and runtime dependencies, excluding test files and build tools from the final image, leveraging layer caching, and include explanations of each optimization with an estimated size reduction.
APPROACH/RISK NOTES:
Explain each optimization step by step and provide a rough estimate of the image size reduction achieved by the multi-stage build.
OPERATIVE TASK ENTITIES (copy each EXACTLY, character-for-character, into the task_entities array AND reproduce each verbatim inside the prompt body):
- Dockerfile
- multi-stage
- slim
- distroless
- layer caching
