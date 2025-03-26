FROM python:3.9-slim

COPY code_int_reqs.txt .
COPY codespaces.py .

RUN pip install -r code_int_reqs.txt

CMD ["python", "codespaces.py"]
