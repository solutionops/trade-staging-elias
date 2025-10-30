# Comandos Docker para la Aplicación de Trading

Este documento contiene los comandos necesarios para construir, ejecutar y gestionar el contenedor Docker de la aplicación de trading.

## ✅ Estado Actual

La aplicación está **funcionando correctamente** con:
- Docker configurado en puerto **8080** (para evitar conflictos con AirPlay en macOS)
- Soporte para cambio de acciones y modelos desde la interfaz web
- Logs visibles en tiempo real para debugging
- Persistencia de datos en el directorio local `data/`

## Comandos Principales

### 1. Construir la Imagen Docker

```bash
docker build -t trading-prediction .
```

Este comando construye la imagen Docker a partir del Dockerfile. Tardará unos minutos la primera vez mientras descarga las dependencias.

### 2. Ejecutar el Contenedor

```bash
docker run -d -p 8080:8080 -v "$(pwd)/data:/app/data" -e HOST=0.0.0.0 -e PORT=8080 --name trading-prediction trading-prediction:latest
```

**Parámetros:**
- `-d`: Ejecuta el contenedor en segundo plano (detached mode)
- `-p 8080:8080`: Mapea el puerto 8080 del contenedor al puerto 8080 de tu máquina
- `-v "$(pwd)/data:/app/data"`: Monta el directorio local `data/` en el contenedor para persistir datos
- `-e HOST=0.0.0.0`: Variable de entorno para el host
- `-e PORT=8080`: Variable de entorno para el puerto
- `--name trading-prediction`: Nombre del contenedor
- `trading-prediction:latest`: Nombre de la imagen a usar

### 3. Ver los Logs del Contenedor

```bash
docker logs trading-prediction
```

Para ver los logs en tiempo real:
```bash
docker logs -f trading-prediction
```

### 4. Detener el Contenedor

```bash
docker stop trading-prediction
```

### 5. Reiniciar el Contenedor

```bash
docker restart trading-prediction
```

### 6. Eliminar el Contenedor

```bash
docker rm -f trading-prediction
```

### 7. Ver Contenedores en Ejecución

```bash
docker ps
```

Para ver todos los contenedores (incluyendo los detenidos):
```bash
docker ps -a
```

### 8. Entrar al Contenedor (Shell)

```bash
docker exec -it trading-prediction /bin/bash
```

## Acceso a la Aplicación

Una vez que el contenedor esté en ejecución, accede a la aplicación web en:

```
http://localhost:8080
```

## Actualización de Datos

Para regenerar los datos y modelos, simplemente reinicia el contenedor:

```bash
docker restart trading-prediction
```

O detén y ejecuta de nuevo:
```bash
docker stop trading-prediction
docker rm trading-prediction
docker run -d -p 8080:8080 -v "$(pwd)/data:/app/data" -e HOST=0.0.0.0 -e PORT=8080 --name trading-prediction trading-prediction:latest
```

## Gestión de la Imagen Docker

### Ver imágenes Docker
```bash
docker images
```

### Eliminar una imagen
```bash
docker rmi trading-prediction:latest
```

### Limpiar imágenes sin usar
```bash
docker image prune -a
```

## Solución de Problemas

### Si el puerto 8080 está ocupado

Cambia el puerto del host en el comando docker run:
```bash
docker run -d -p 9090:8080 ...  # Usa 9090 en lugar de 8080
```

Luego accede a `http://localhost:9090`

### Si hay conflictos con el nombre del contenedor

Elimina el contenedor existente primero:
```bash
docker rm -f trading-prediction
```

### Ver logs de error
```bash
docker logs trading-prediction 2>&1 | tail -50
```

## Archivos Persistidos

Los siguientes archivos se guardan en el directorio `data/` local y persisten aunque el contenedor se elimine:

- `data/stock_data.xlsx`: Datos históricos de la acción
- `data/model_prediction.json`: Modelo entrenado y predicciones

## Nota sobre Puerto 5000

El puerto 5000 por defecto puede estar ocupado en macOS por AirPlay Receiver. Por eso usamos el puerto 8080 en esta configuración.

