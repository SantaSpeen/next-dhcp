FROM python:3.13.2-alpine
LABEL authors="santaspeen"

COPY requirements.txt /app/
COPY src/ /app/

WORKDIR /app
RUN pip install --no-cache-dir -r requirements.txt

ENTRYPOINT ["python", "main.py"]