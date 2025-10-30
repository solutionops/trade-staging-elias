# Modelos Implementados - Sistema de Trading

## ✅ Funcionalidades Implementadas

### 1. Selector de Modelos
- **Polynomial Regression**: Modelo polinomial de grado 3 (implementado)
- **Neural Network (MLP)**: Red neuronal con MLPRegressor (implementado)

### 2. Recalibración Automática
Todas las predicciones se ajustan con el precio actual:
```python
offset = current_price - predicted_today
adjusted_forecast = forecast + offset
```

### 3. Features del MLP
- Lags: Close(t-1) hasta Close(t-10)
- Retornos: 1 día y 5 días
- Medias móviles: SMA 5 y SMA 10
- Volatilidad: Desviación estándar 10 días
- Estandarización: StandardScaler

### 4. Predicción
- 30 días hacia adelante
- Mismo intervalo que entrenamiento (diario)
- Recalibración aplicada

## 📊 Cómo Usar

1. Abre http://127.0.0.1:8080
2. Selecciona empresa (INTC, AMZN, ORCL, NVDA, MELI)
3. Selecciona modelo (Polynomial o Neural Network)
4. Click en "Actualizar Datos"
5. Espera a que se genere la predicción

## 🎯 Diferencias entre Modelos

### Polynomial Regression
- Más rápido
- Interpretable
- Buen ajuste a tendencias
- R² típico: 79-80%

### Neural Network (MLP)
- Más complejo
- Puede capturar patrones no lineales
- Requiere más datos
- R² típico: 80-85%

## ⚙️ Configuración MLP
```python
MLPRegressor(
    hidden_layer_sizes=(64, 32),
    activation='relu',
    learning_rate_init=1e-3,
    max_iter=800,
    early_stopping=True,
    n_iter_no_change=20,
    random_state=42
)
```

## 📈 Variables Predichas
- Open (apertura)
- High (máximo)
- Low (mínimo)
- Close (cierre)
