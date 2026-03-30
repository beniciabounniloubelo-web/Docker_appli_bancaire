FROM python:3.9-slim

WORKDIR /app

# Installer les dépendances nécessaires pour psycopg2
RUN apt-get update && apt-get install -y libpq-dev gcc

# Copier les dépendances Python
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copier le script
COPY . .
