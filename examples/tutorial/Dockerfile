FROM python:3.11.2-alpine3.17

COPY . "/tutorial"
WORKDIR /tutorial

RUN pip install .
RUN flask --app=flaskr init-db

EXPOSE 5000

CMD [ "flask", "--app=flaskr", "run", "--host=0.0.0.0"]