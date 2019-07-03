FROM python:3.7-alpine

EXPOSE 8000

RUN mkdir -p /app
WORKDIR /app

RUN pip install pipenv
RUN apk add --no-cache build-base

COPY Pipfile .
COPY Pipfile.lock .

RUN pipenv install --deploy --system

RUN apk del build-base

COPY . .

CMD ["python", "main.py"]
