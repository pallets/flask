FROM python:3.12-slim

WORKDIR /app

COPY . .
RUN pip install --no-cache-dir .

EXPOSE 5000

CMD flask --app flaskr init-db && flask --app flaskr run --host=0.0.0.0