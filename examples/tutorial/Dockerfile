FROM python:3-alpine

ADD . /app
WORKDIR /app
RUN pip install -e .
ENV FLASK_APP flaskr
ENV FLASK_ENV development
RUN flask init-db

ENTRYPOINT ["flask"]
CMD ["run","--host","0.0.0.0"]
