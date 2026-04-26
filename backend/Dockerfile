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
ENV ENV=production

# Entrypoint que aplica migraciones y arranca uvicorn
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 8000

CMD ["/entrypoint.sh"]
