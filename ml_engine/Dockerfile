FROM python:3.11-slim

# Évite les .pyc + logs python non flush
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Dossier de travail
WORKDIR /app

# Dépendances système (utile pour sklearn/numpy et pour le healthcheck curl)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Installer les dépendances Python en 2 étapes (cache Docker efficace)
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copier le code (en dev, le volume docker-compose peut écraser cette copie)
COPY . /app

# Port du service Flask
EXPOSE 5000

# Lancement
CMD ["python", "app.py"]
