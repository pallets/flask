FROM python:latest
COPY . .
CMD python3 -m pip install -r requirements/docs.txt
RUN python3 -m flask run

