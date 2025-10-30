# Dockerfile para Trading Prediction System

FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación
COPY . .

# Crear directorio para datos generados
RUN mkdir -p /app/data

# Exponer el puerto
EXPOSE 8080

# Comando para iniciar la aplicación
CMD ["sh", "-c", "python getData.py && python web_app.py"]
