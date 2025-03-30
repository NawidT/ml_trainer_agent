FROM python:3.9-slim

WORKDIR /app

COPY code_int_reqs.txt .
RUN pip install -r code_int_reqs.txt

RUN mkdir tmp

COPY tmp/codespace.py ./tmp/
COPY tmp/memory.pkl ./tmp/

CMD ["python", "/app/tmp/codespace.py"]
