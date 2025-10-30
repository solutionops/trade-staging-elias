# Dockerfile para Trading Prediction System

FROM python:3.11-slim

# Establecer directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    cron \
    tzdata \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY requirements.txt .

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r requirements.txt

# Copiar toda la aplicación
COPY . .

# Crear directorio para datos generados
RUN mkdir -p /app/data /var/log

# Zona horaria: Chile
ENV TZ=America/Santiago
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Registrar cron a las 05:00 Chile
COPY crontab.txt /etc/cron.d/trading-cron
RUN chmod 0644 /etc/cron.d/trading-cron && crontab /etc/cron.d/trading-cron && touch /var/log/cron.log

# Exponer el puerto
EXPOSE 8080

# Comando para iniciar la aplicación
CMD ["sh", "-c", "cron && python getData.py && python web_app.py"]
