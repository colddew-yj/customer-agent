# customer-helpmesh-agent (FastAPI + LangGraph)
#
# Build:
#   docker build -t customer-helpmesh-agent:latest .
#
# Run:
#   docker run --rm -p 8000:8000 \
#     -v $(pwd)/agent.yaml:/app/agent.yaml:ro \
#     -v $(pwd)/knowledge:/app/knowledge:ro \
#     -v customer-helpmesh-agent-data:/app/data \
#     customer-helpmesh-agent:latest

FROM python:3.11-slim

WORKDIR /app

ENV PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple \
    PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY agent/ /app/agent/
COPY pyproject.toml /app/pyproject.toml
COPY README.md /app/README.md

RUN mkdir -p /app/data /app/knowledge
VOLUME ["/app/data"]

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -fsS http://localhost:8000/health || exit 1

CMD ["uvicorn", "agent.server:app", "--host", "0.0.0.0", "--port", "8000"]