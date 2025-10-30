# Instrucciones Docker - Trading Prediction System

## 📦 Preparación

### 1. Asegúrate de tener Docker instalado

Verificar:
```bash
docker --version
docker-compose --version
```

Si no lo tienes, instálalo desde: https://docs.docker.com/get-docker/

## 🚀 Comandos Básicos

### Construir la imagen
```bash
docker build -t trading-prediction .
```

### Ejecutar el contenedor
```bash
docker run -d -p 5000:5000 --name trading-app trading-prediction
```

### Con Docker Compose (recomendado)
```bash
# Construir y ejecutar
docker-compose up -d

# Ver logs
docker-compose logs -f

# Detener
docker-compose down
```

## 🌐 Acceso

Una vez levantado, accede a:
```
http://localhost:5000
```

## 📋 Comandos Útiles

### Ver logs en tiempo real
```bash
docker logs -f trading-app
```

### Detener el contenedor
```bash
docker stop trading-app
```

### Iniciar el contenedor
```bash
docker start trading-app
```

### Eliminar el contenedor
```bash
docker rm trading-app
```

### Reconstruir la imagen
```bash
docker-compose build --no-cache
docker-compose up -d
```

### Ejecutar comandos dentro del contenedor
```bash
docker exec -it trading-app bash
```

### Ver información del contenedor
```bash
docker ps
```

## 🔧 Solución de Problemas

### Si el puerto 5000 está ocupado:
```bash
# Cambiar en docker-compose.yml
ports:
  - "8080:5000"  # Puerto externo:puerto interno
```

### Ver logs de errores:
```bash
docker-compose logs trading-app
```

### Reiniciar el contenedor:
```bash
docker-compose restart
```

## 📁 Estructura de Datos

Los datos generados se guardan en:
- Local: `./data/` (directorio en tu máquina)
- Docker: `/app/data/` (dentro del contenedor)

Los archivos `.xlsx` y `.json` se persisten entre reinicios gracias al volumen.

## 🚢 Para Producción (Web)

### Opción A: Docker Hub

1. Crear cuenta en https://hub.docker.com
2. Tag de la imagen:
```bash
docker tag trading-prediction tu-usuario/trading-prediction
```

3. Subir:
```bash
docker push tu-usuario/trading-prediction
```

4. En el servidor:
```bash
docker pull tu-usuario/trading-prediction
docker run -d -p 80:5000 tu-usuario/trading-prediction
```

### Opción B: Servicios Cloud

#### Heroku:
```bash
heroku create trading-prediction
heroku container:push web
heroku container:release web
```

#### AWS ECS / Google Cloud Run / Azure Container Instances:
- Usa la imagen de Docker Hub o construye en su plataforma

#### DigitalOcean App Platform:
- Conecta tu repositorio GitHub y despliega automáticamente

## ⚠️ Notas Importantes

1. **Volúmenes**: Los datos se guardan en `./data/` en tu máquina
2. **Puerto**: Por defecto usa 5000, puedes cambiar en docker-compose.yml
3. **Memoria**: El MLP puede consumir memoria, asegúrate de tener suficiente
4. **Internet**: Necesita conexión para descargar datos de yfinance

## 📊 Variables de Entorno

Puedes configurar:
```yaml
environment:
  - HOST=0.0.0.0
  - PORT=5000
```
