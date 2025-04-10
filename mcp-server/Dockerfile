FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY state_brewery_mcp_server.py .

EXPOSE 3000

CMD ["python", "state_brewery_mcp_server.py"]