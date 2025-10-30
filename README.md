# Sistema de Predicción de Trading - Intel (INTC)

Sistema completo de análisis y predicción de acciones con regresión polinomial y visualización web.

## 🎯 Características

- ✅ Descarga de datos históricos en intervalos de 5 minutos
- ✅ Almacenamiento de datos en Excel
- ✅ Modelo de regresión polinomial de grado 3
- ✅ Predicción del comportamiento del próximo mes
- ✅ Visualización web interactiva y moderna

## 📦 Instalación

1. **Instala las dependencias necesarias:**

```bash
pip install -r requirements.txt
```

## 🚀 Uso

**IMPORTANTE:** Se recomienda usar un entorno virtual para evitar conflictos de dependencias.

### Paso 0: Crear y activar el entorno virtual

```bash
# Crear entorno virtual
python3 -m venv venv

# Activar el entorno virtual
source venv/bin/activate  # En macOS/Linux
# o
venv\Scripts\activate  # En Windows
```

### Paso 1: Obtener datos y generar predicciones

Ejecuta el script principal para descargar los datos (últimos 90 días en intervalos de 1 hora), entrenar el modelo y generar las predicciones:

```bash
python getData.py
```

Este script realizará:
1. Descarga de datos de INTC en intervalos de 1 hora (últimos 3 meses/90 días)
2. Limpieza de datos nulos
3. Guardado de datos en `stock_data.xlsx`
4. Entrenamiento de un modelo de regresión polinomial
5. Predicción del próximo mes
6. Generación de un gráfico y guardado en `model_prediction.json`

### Paso 2: Iniciar el servidor web

Una vez que hayas ejecutado `getData.py`, inicia el servidor web:

```bash
python web_app.py
```

### Paso 3: Visualizar resultados

Abre tu navegador y accede a:
```
http://127.0.0.1:5000
```

## 📊 Características de la Web

- **Estadísticas en tiempo real**: Visualización de puntos históricos, predichos, precios actuales y futuros
- **Gráfico interactivo**: Muestra datos históricos, ajuste del modelo y predicciones futuras
- **Descarga de Excel**: Botón para descargar los datos históricos en formato Excel
- **Diseño moderno**: Interfaz responsive con diseño gradiente profesional

## 📁 Archivos Generados

- `stock_data.xlsx`: Datos históricos en formato Excel
- `model_prediction.json`: Datos del modelo y predicciones para la visualización web

## ⚙️ Configuración

Puedes modificar los parámetros en `getData.py`:

- **Ticker**: Cambia `"INTC"` por otro símbolo de acción (por ejemplo: "AAPL", "GOOGL", "MSFT")
- **Intervalo**: Actualmente configurado en `"1h"` (1 hora). Otros intervalos disponibles: "1m", "5m", "15m", "1d"
- **Días**: Cambia `days=90` para obtener más o menos datos históricos:
  - **5m, 15m**: máximo 60 días
  - **1h**: máximo 730 días (~2 años) ✅
  - **1d**: sin límite práctico
- **Grado polinomial**: Cambia `degree=3` en la función `train_polynomial_model` (3 es un buen balance)

## 🔧 Estructura del Proyecto

```
trading/
├── getData.py           # Script principal de análisis y predicción
├── web_app.py           # Aplicación web Flask
├── requirements.txt     # Dependencias del proyecto
├── README.md            # Este archivo
├── venv/                # Entorno virtual (no incluido en git)
├── stock_data.xlsx      # Datos históricos (generado)
└── model_prediction.json # Datos del modelo (generado)
```

## 📝 Notas Importantes

- La descarga de datos puede tardar varios minutos dependiendo del intervalo y período solicitado
- **Intervalos y límites de datos históricos:**
  - 5m, 15m: máximo 60 días
  - 1h: hasta 730 días (2 años) ✅ **Recomendado para 3 meses**
  - 1d: sin límite
- Si falla la descarga con un intervalo, el script automáticamente intentará con otro intervalo
- Las predicciones son estimaciones basadas en tendencias y no deben considerarse consejos de inversión
- El modelo usa regresión polinomial de grado 3, que captura tendencias no lineales en los datos

## 🛠️ Tecnologías Utilizadas

- **yfinance**: Descarga de datos financieros
- **pandas**: Manipulación de datos
- **scikit-learn**: Machine Learning (regresión polinomial)
- **matplotlib**: Visualización de datos
- **flask**: Framework web
- **openpyxl**: Manejo de archivos Excel
