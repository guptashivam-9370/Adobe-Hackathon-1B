FROM python:3.9-slim

WORKDIR /app

# Install build tools if needed
RUN apt-get update && apt-get install -y build-essential gcc

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY download_model.py .
RUN python download_model.py

COPY . .

CMD ["python", "run_1b.py", "Challenge_1b/Collection 1"]