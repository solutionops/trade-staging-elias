# Plan de Implementación - MLP y Modelo Dual

## Resumen
El archivo actual tiene 444 líneas y necesita incorporar:
1. Modelo MLP (Red Neuronal) junto al existente Polynomial
2. Recalibración con precio actual
3. Predicción recursiva para 30 días
4. Selector de modelo en la UI

## Archivos a modificar
- `getData.py` - Backend (Python)
- `web_app.py` - Frontend (Flask + HTML/JS)

## Funcionalidades ya implementadas
- ✅ build_features() - líneas 70-106
- ✅ train_mlp_model() - líneas 108-139
- ✅ Imports necesarios (StandardScaler, MLPRegressor)

## Funcionalidades pendientes

### 1. Recalibración (NUEVA)
```python
def recalibrate_predictions(forecast, current_price, predicted_today):
    """
    Ajusta las predicciones aplicando un offset basado en el precio actual
    """
    offset = current_price - predicted_today
    adjusted_forecast = forecast + offset
    return adjusted_forecast
```

### 2. Predicción Recursiva para MLP (NUEVA)
```python
def predict_recursive_mlp(mlp_model, scaler, feature_names, data_history, n_days=30):
    """
    Predice n días hacia adelante usando predicción recursiva
    Cada día usa las predicciones anteriores para construir features
    """
    predictions = []
    # Construir ventana inicial desde datos históricos
    # Por cada día futuro:
    #   - Construir features con la ventana actual
    #   - Predecir Close del siguiente día
    #   - Agregar predicción a la ventana
    # Retornar predicciones
```

### 3. Modificar main() para soportar ambos modelos
- Añadir parámetro model_type="polynomial" (default)
- Train según el modelo seleccionado
- Predecir según el modelo
- Aplicar recalibración
- Guardar tipo de modelo en output

### 4. Selector en web_app.py
- Añadir dropdown con opciones: "Polynomial", "NeuralNetwork"
- Modificar API para recibir model_type
- Actualizar visualización con el modelo seleccionado

## Decisión requerida

Debido a la complejidad, tengo dos opciones:

### Opción A: Implementación completa por partes
- Paso 1: Recalibración
- Paso 2: Predicción recursiva MLP
- Paso 3: Integración en main()
- Paso 4: Selector UI

### Opción B: Reescribir archivo completo
- Crear getData_v2.py con todo integrado
- Probar funciona
- Reemplazar original

¿Cuál prefieres?
