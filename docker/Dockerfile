FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .[all]

ENTRYPOINT ["python", "-m", "erpnext_agent.mcp_server"]
