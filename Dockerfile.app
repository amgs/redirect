FROM python:3.10-slim
WORKDIR /app
RUN apt update && apt install -y iputils-ping
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src/* .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]