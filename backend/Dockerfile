FROM python:3.11-slim

WORKDIR /app

# Dependencias del sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Dependencias Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Código fuente
COPY . .

# Crear directorios de datos
RUN mkdir -p /app/data /app/uploads/faces

# Variables por defecto (se sobreescriben con env vars en Coolify)
ENV DATABASE_URL=sqlite:////app/data/gimnasio.db
ENV UPLOAD_DIR=/app/uploads
ENV FACES_DIR=/app/uploads/faces

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
