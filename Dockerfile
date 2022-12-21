FROM python:3.8-alpine

WORKDIR /work

COPY . .

RUN pip install --no-cache-dir -e .

ENTRYPOINT [ "python", "-m", "vwkommi" ]
