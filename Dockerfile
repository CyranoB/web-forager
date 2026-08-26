FROM python:3.12-slim AS builder

WORKDIR /app

# Version for setuptools_scm (required since .git is not copied)
# Override at build time with: docker build --build-arg VERSION=x.y.z
ARG VERSION=0.0.0
ENV SETUPTOOLS_SCM_PRETEND_VERSION=${VERSION}

# Install uv as a pinned wheel, then install only locked binary dependencies.
RUN python -m pip install --no-cache-dir --only-binary=:all: uv==0.11.6
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --locked --no-dev --no-install-project --no-build
COPY src/ ./src/
RUN uv build --wheel \
    && uv pip install --python .venv/bin/python --no-deps --only-binary=:all: dist/*.whl

FROM python:3.12-slim AS runtime

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

# Create a non-root user for security.
RUN useradd --create-home --shell /bin/bash appuser
USER appuser

# Run the MCP server
ENTRYPOINT ["/app/.venv/bin/web-forager", "serve"]
