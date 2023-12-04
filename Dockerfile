FROM python:latest

WORKDIR /src/flask

COPY ./examples/tutorial /src/flask

RUN pip install -e .
RUN pip install --upgrade pip
RUN flask --app flaskr init-db
CMD flask --app flaskr run --debug --host 0.0.0.0
