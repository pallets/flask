FROM python:3.12-slim

WORKDIR /app

COPY . .

RUN pip install -e .

EXPOSE 5000

CMD ["flask", "--app", "flaskr", "run", "--host=0.0.0.0"]
