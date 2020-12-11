FROM 10.12.6.31:9088/python-3.7-alpine:latest

RUN pip install flask

WORKDIR client

COPY main.py main.py

CMD ["python", "main.py"]

EXPOSE 7000
