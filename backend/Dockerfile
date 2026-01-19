# Wir nutzen ein schmales Python Image
FROM python:3.11-slim

# Arbeitsverzeichnis setzen
WORKDIR /code

# Abhängigkeiten installieren
COPY ./requirements.txt /code/requirements.txt
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Code kopieren
COPY ./app /code/app

# Port öffnen (Coolify Default ist oft 8000, wir nutzen 80)
EXPOSE 80

# Server starten
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]
