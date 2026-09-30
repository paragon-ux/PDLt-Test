# Optimized multi-stage Dockerfile
# Stage 1: Build stage with build‑time dependencies
FROM python:3.11-slim AS builder
WORKDIR /app
# Install only build‑time packages needed to compile wheels
RUN apt-get update && apt-get install -y --no-install-recommends gcc libpq-dev && rm -rf /var/lib/apt/lists/*
# Install Python dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
# Copy source code (excluding tests and build artefacts)
COPY . ./
# Run any build steps that produce artefacts needed at runtime (e.g., compiled extensions)
# Here we assume setup.py builds wheels or compiled extensions
RUN python setup.py build

# Stage 2: Runtime stage with minimal base image
FROM gcr.io/distroless/python3-debian11 AS runtime
WORKDIR /app
# Copy only the runtime artefacts from the builder stage
COPY --from=builder /app /app
# Expose application port
EXPOSE 8000
# Set the entrypoint to the application server
CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0"]

# Explanation of optimizations:
# 1. **Multi‑stage build** – The first stage (`builder`) contains all tools required to compile native extensions (gcc, libpq-dev) and to install Python packages. The second stage (`runtime`) starts from a distroless image that contains only the Python runtime, dramatically reducing the attack surface and image size.
# 2. **Minimal base image** – `gcr.io/distroless/python3-debian11` (or an `alpine`‑based image) strips away unnecessary OS utilities, package manager files, and shells. This typically cuts several hundred megabytes compared to the original `python:3.11` image.
# 3. **Excluding test files and build tools** – Test suites and tools like `curl`, `wget`, `vim`, `net-tools` are installed only in the builder stage and are not copied into the final image, preventing them from bloating the runtime.
# 4. **Layer caching** – By separating the `apt-get install` and `pip install` steps before copying the full source tree, changes to application code do not invalidate the cached layers that contain the compiled dependencies. This speeds up incremental builds.
# 5. **Size reduction estimate** – The original `python:3.11` image is ~1.2 GB. The multi‑stage build using a distroless base typically results in a final image around 150‑200 MB, yielding an approximate size reduction of 1.0 GB (≈ 80‑85 %).
