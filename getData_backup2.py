import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import PolynomialFeatures, StandardScaler
from sklearn.linear_model import LinearRegression
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
import json
import base64
from io import BytesIO

def get_stock_data(ticker="INTC", interval="1d", days=365):
    """
    Obtiene datos históricos de una acción en intervalos específicos
    desde hace N días hasta hoy
    """
    end_date = datetime.now()
    
    start_date = end_date - timedelta(days=days)
    
    print(f"Descargando datos desde {start_date.strftime('%Y-%m-%d')} hasta {end_date.strftime('%Y-%m-%d')}...")
    print(f"Intervalo: {interval}")
    
    try:
        data = yf.download(
            ticker, 
            interval=interval, 
            start=start_date.strftime('%Y-%m-%d'), 
            end=end_date.strftime('%Y-%m-%d'),
            progress=False
        )
        
        # Si no hay datos, intentar con período predeterminado
        if data.empty:
            print("No se obtuvieron datos con el rango especificado. Intentando descarga automática...")
            data = yf.download(ticker, interval=interval, period="60d", progress=False)
        
        data = data.dropna()
        print(f"Datos descargados: {len(data)} registros")
        
        if len(data) == 0:
            raise ValueError("No se pudieron obtener datos. Verifica que el ticker sea válido y que haya datos disponibles.")
        
    except Exception as e:
        print(f"Error al descargar datos: {e}")
        print("Intentando con intervalo de 15 minutos...")
        try:
            data = yf.download(ticker, interval="15m", period="60d", progress=False)
            data = data.dropna()
            print(f"Datos descargados con intervalo 15m: {len(data)} registros")
        except:
            print("No se pudieron obtener datos con ningún intervalo")
            data = pd.DataFrame()
    
    return data

def save_to_excel(data, filename="stock_data.xlsx"):
    """
    Guarda los datos en un archivo Excel
    """
    # Remover timezone si existe para compatibilidad con Excel
    data_copy = data.copy()
    if data_copy.index.tz is not None:
        data_copy.index = data_copy.index.tz_localize(None)
    
    data_copy.to_excel(filename)
    print(f"Datos guardados en {filename}")

def build_features(df, lookback=10):
    """
    Construye features para el modelo MLP usando lags, retornos, SMAs y volatilidad
    
    Args:
        df: DataFrame con precios (debe tener columna 'Close')
        lookback: Número de días históricos a usar
    
    Returns:
        DataFrame con features, serie objetivo y lista de columnas
    """
    features_df = pd.DataFrame()
    
    # Lags del precio Close
    for i in range(1, min(lookback + 1, 11)):
        features_df[f'lag_{i}'] = df['Close'].shift(i)
    
    # Retornos
    features_df['ret_1'] = df['Close'].pct_change(1)
    features_df['ret_5'] = df['Close'].pct_change(5)
    
    # Medias móviles
    features_df['sma_5'] = df['Close'].rolling(window=5).mean()
    features_df['sma_10'] = df['Close'].rolling(window=10).mean()
    
    # Volatilidad (std de retornos)
    features_df['vol_10'] = df['Close'].pct_change().rolling(window=10).std()
    
    # Objetivo: Close actual
    y = df['Close'].values
    
    # Eliminar filas con NaN
    valid_idx = ~features_df.isna().any(axis=1)
    features_df = features_df[valid_idx].reset_index(drop=True)
    y = y[valid_idx]
    
    return features_df, y, features_df.columns.tolist()

def train_mlp_model(data):
    """
    Entrena un modelo MLP para predecir Close usando features de ingeniería
    """
    # Construir features
    X_features, y_target, feature_names = build_features(data)
    
    # Estandarizar features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_features)
    
    # Entrenar MLP
    mlp = MLPRegressor(
        hidden_layer_sizes=(64, 32),
        activation='relu',
        learning_rate_init=1e-3,
        max_iter=800,
        early_stopping=True,
        n_iter_no_change=20,
        random_state=42,
        shuffle=False  # Respetar orden temporal
    )
    
    mlp.fit(X_scaled, y_target)
    
    # Predecir sobre datos históricos para evaluar
    y_pred_hist = mlp.predict(X_scaled)
    r2_score = mlp.score(X_scaled, y_target)
    
    print(f"Modelo MLP Close - R² Score: {r2_score:.4f}")
    
    return mlp, scaler, X_scaled, y_pred_hist, feature_names

def train_polynomial_model(data, degree=3):
    """
    Entrena modelos de regresión polinomial para Open, High, Low y Close
    """
    X = np.arange(len(data)).reshape(-1, 1)
    
    # Entrenar modelos para cada métrica
    models = {}
    predictions = {}
    
    for column in ['Open', 'High', 'Low', 'Close']:
        y = data[column].values
        
        model = Pipeline([
            ('poly', PolynomialFeatures(degree=degree)),
            ('linear', LinearRegression())
        ])
        
        model.fit(X, y)
        y_pred = model.predict(X)
        
        models[column] = model
        predictions[column] = y_pred
        
        print(f"Modelo {column} - R² Score: {model.score(X, y):.4f}")
    
    print(f"Modelos entrenados con grado polinomial: {degree}")
    
    return models, X, predictions

def predict_next_month(models, historical_length, interval="1d"):
    """
    Predice el comportamiento del próximo mes usando todos los modelos (Open, High, Low, Close)
    Usa el mismo intervalo del entrenamiento
    """
    # Calcular puntos de predicción según el intervalo
    if interval == "1d":
        # Para 1 día: predecir 30 días hacia adelante
        next_month_points = 30
    elif interval == "1h":
        # Para 1 hora: 30 días * 24 horas
        next_month_points = int(30 * 24)
    elif interval == "5m":
        # Para 5 minutos: 30 días * 24 horas * 12 intervalos
        next_month_points = int(30 * 24 * 12)
    elif interval == "15m":
        # Para 15 minutos: 30 días * 24 horas * 4 intervalos
        next_month_points = int(30 * 24 * 4)
    else:
        # Default: 30 días
        next_month_points = 30
    
    X_future = np.arange(historical_length, historical_length + next_month_points).reshape(-1, 1)
    
    # Predecir con todos los modelos
    predictions = {}
    for column in ['Open', 'High', 'Low', 'Close']:
        predictions[column] = models[column].predict(X_future)
    
    print(f"Predicción generada para {next_month_points} puntos (1 mes - intervalo: {interval})")
    
    return X_future, predictions

def generate_future_dates(start_date, num_intervals, freq="1D"):
    """
    Genera fechas futuras para la predicción según el intervalo
    """
    if freq == "1D":
        end_date = start_date + timedelta(days=num_intervals)
    elif freq == "1h" or freq == "1H":
        end_date = start_date + timedelta(hours=num_intervals)
    elif freq == "5min":
        end_date = start_date + timedelta(minutes=5 * num_intervals)
    elif freq == "15min":
        end_date = start_date + timedelta(minutes=15 * num_intervals)
    else:
        end_date = start_date + timedelta(days=num_intervals)
    
    return pd.date_range(start=start_date, end=end_date, freq=freq)[:num_intervals]

def create_plot(data, predictions_hist, future_dates, predictions_future, ticker="INTC"):
    """
    Crea un gráfico con los datos históricos, el ajuste del modelo y las predicciones futuras
    """
    plt.figure(figsize=(20, 10))
    
    # Datos históricos reales
    plt.plot(data.index, data['Close'].values, label='Precio Real Histórico', 
             linewidth=2, color='blue', alpha=0.7)
    
    # Ajuste del modelo para Close
    plt.plot(data.index, predictions_hist['Close'], label='Modelo Close (Regresión Polinomial)', 
             linewidth=2, color='red', linestyle='--', alpha=0.8)
    
    # Predicciones futuras para Close
    plt.plot(future_dates, predictions_future['Close'], label='Predicción Close Próximo Mes', 
             linewidth=2, color='green', alpha=0.8)
    
    # Predicciones futuras para High (máximo del día)
    plt.plot(future_dates, predictions_future['High'], label='Predicción High (Máximo)', 
             linewidth=1.5, color='orange', linestyle=':', alpha=0.7)
    
    # Predicciones futuras para Low (mínimo del día)
    plt.plot(future_dates, predictions_future['Low'], label='Predicción Low (Mínimo)', 
             linewidth=1.5, color='purple', linestyle=':', alpha=0.7)
    
    # Línea vertical separando histórico de predicción
    plt.axvline(x=data.index[-1], color='gray', linestyle=':', linewidth=2, label='Hoy', alpha=0.6)
    
    # Agregar fechas y precios en puntos clave de la predicción futura
    if len(future_dates) > 0 and len(predictions_future['Close']) > 0:
        # Convertir a valores escalares si son arrays numpy
        y_start = float(predictions_future['Close'][0]) if hasattr(predictions_future['Close'][0], 'item') else predictions_future['Close'][0]
        y_end = float(predictions_future['Close'][-1]) if hasattr(predictions_future['Close'][-1], 'item') else predictions_future['Close'][-1]
        
        # Marcar inicio de predicción
        plt.annotate(f'Inicio\n{future_dates[0].strftime("%d/%m")}\n${y_start:.2f}',
                    xy=(future_dates[0], y_start), 
                    xytext=(10, 30), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='green', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                    fontsize=9, fontweight='bold', color='white')
        
        # Marcar punto medio de predicción (si hay suficientes datos)
        if len(future_dates) > 10:
            mid_point = len(future_dates) // 2
            y_mid = float(predictions_future['Close'][mid_point]) if hasattr(predictions_future['Close'][mid_point], 'item') else predictions_future['Close'][mid_point]
            plt.annotate(f'{future_dates[mid_point].strftime("%d/%m")}\n${y_mid:.2f}',
                        xy=(future_dates[mid_point], y_mid), 
                        xytext=(10, -40), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', fc='orange', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                        fontsize=9, fontweight='bold', color='white')
        
        # Marcar final de predicción
        plt.annotate(f'Final\n{future_dates[-1].strftime("%d/%m")}\n${y_end:.2f}',
                    xy=(future_dates[-1], y_end), 
                    xytext=(-50, 30), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='darkgreen', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                    fontsize=9, fontweight='bold', color='white')
    
    plt.xlabel('Fecha', fontsize=12, fontweight='bold')
    plt.ylabel('Precio (USD)', fontsize=12, fontweight='bold')
    plt.title(f'{ticker} - Análisis con Regresión Polinomial y Predicción del Próximo Mes\nIntervalo: Diario (1 año histórico)', 
              fontsize=14, fontweight='bold')
    plt.legend(loc='best', fontsize=10)
    plt.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    # Guardar gráfico en buffer
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=100)
    buf.seek(0)
    image_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()
    
    return image_base64

def get_ticker_name(ticker_symbol):
    """
    Devuelve el nombre de la empresa dado su símbolo
    """
    ticker_names = {
        "INTC": "Intel",
        "AMZN": "Amazon",
        "ORCL": "Oracle",
        "NVDA": "NVIDIA",
        "MELI": "MercadoLibre"
    }
    return ticker_names.get(ticker_symbol, ticker_symbol)

def main(ticker="INTC"):
    """
    Función principal que ejecuta todo el pipeline
    """
    # 1. Obtener datos históricos
    print("=" * 60)
    print(f"PASO 1: Obteniendo datos históricos de {get_ticker_name(ticker)} ({ticker})")
    print("=" * 60)
    data = get_stock_data(ticker=ticker, interval="1d", days=365)  # 1 año en intervalos diarios
    
    # 2. Guardar en Excel
    print("\n" + "=" * 60)
    print("PASO 2: Guardando datos en Excel")
    print("=" * 60)
    save_to_excel(data, "stock_data.xlsx")
    
    # 3. Entrenar modelos
    print("\n" + "=" * 60)
    print("PASO 3: Entrenando modelos de regresión polinomial (Open, High, Low, Close)")
    print("=" * 60)
    models, X, predictions_hist = train_polynomial_model(data, degree=3)
    
    # 4. Predecir próximo mes
    print("\n" + "=" * 60)
    print("PASO 4: Generando predicción del próximo mes")
    print("=" * 60)
    interval = "1d"  # Intervalo usado (diario)
    X_future, predictions_future = predict_next_month(models, len(data), interval=interval)
    
    # Generar fechas futuras según el intervalo
    if interval == "1d":
        freq = "1D"  # Intervalo diario
    elif interval == "1h":
        freq = "1h"
    elif interval == "5m":
        freq = "5min"
    elif interval == "15m":
        freq = "15min"
    else:
        freq = "1D"
    
    future_dates = generate_future_dates(data.index[-1], len(predictions_future['Close']), freq=freq)
    
    # 5. Crear gráfico
    print("\n" + "=" * 60)
    print("PASO 5: Generando gráfico")
    print("=" * 60)
    image_base64 = create_plot(data, predictions_hist, future_dates, predictions_future, ticker=ticker)
    
    # 6. Guardar información del modelo para la web
    # Convertir arrays numpy a valores escalares correctamente para Close
    close_predictions = predictions_future['Close']
    if isinstance(close_predictions, np.ndarray):
        pred_next = float(close_predictions.item(0)) if close_predictions.size > 0 else 0.0
        pred_final = float(close_predictions.item(-1)) if close_predictions.size > 0 else 0.0
    else:
        pred_next = float(close_predictions[0]) if len(close_predictions) > 0 else 0.0
        pred_final = float(close_predictions[-1]) if len(close_predictions) > 0 else 0.0
    
    # Guardar datos completos de predicción para consulta por fecha (incluir High, Low, Close)
    prediction_data = []
    for i, date in enumerate(future_dates):
        day_data = {}
        for col in ['Open', 'High', 'Low', 'Close']:
            val = predictions_future[col][i]
            if isinstance(val, np.ndarray):
                day_data[col.lower()] = float(val.item())
            else:
                day_data[col.lower()] = float(val)
        
        prediction_data.append({
            'date': date.strftime('%Y-%m-%d'),
            **day_data
        })
    
    model_data = {
        'image_base64': image_base64,
        'historical_points': len(data),
        'predicted_points': len(close_predictions),
        'last_price': float(data['Close'].iloc[-1]),
        'predicted_next_price': pred_next,
        'predicted_final_price': pred_final,
        'r2_score': float(models['Close'].score(X, data['Close'].values)),
        'ticker': ticker,
        'ticker_name': get_ticker_name(ticker),
        'prediction_start_date': future_dates[0].strftime('%Y-%m-%d') if len(future_dates) > 0 else '',
        'prediction_end_date': future_dates[-1].strftime('%Y-%m-%d') if len(future_dates) > 0 else '',
        'prediction_data': prediction_data  # Datos completos para consulta por fecha (Open, High, Low, Close)
    }
    
    with open('model_prediction.json', 'w') as f:
        json.dump(model_data, f)
    
    print("\n" + "=" * 60)
    print("PROCESO COMPLETADO")
    print("=" * 60)
    print(f"✓ Empresa: {get_ticker_name(ticker)} ({ticker})")
    print(f"✓ Precio actual: ${model_data['last_price']:.2f}")
    print(f"✓ Predicción inicial: ${pred_next:.2f}")
    print(f"✓ Predicción final: ${pred_final:.2f}")
    print(f"✓ Variación estimada: {((pred_final - model_data['last_price']) / model_data['last_price'] * 100):.2f}%")
    print(f"✓ Datos guardados en: stock_data.xlsx")
    print(f"✓ Modelo y predicción guardados en: model_prediction.json")
    print(f"✓ Puedes ejecutar el servidor web con: python web_app.py")
    print("=" * 60)
    
    return model_data

if __name__ == "__main__":
    # Importar matplotlib aquí para evitar problemas en la app web
    import matplotlib
    matplotlib.use('Agg')  # Backend no interactivo para servidor
    import matplotlib.pyplot as plt
    
    import sys
    
    # Permitir pasar el ticker como argumento
    ticker = "INTC"  # Default
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
    
    try:
        main(ticker=ticker)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nSugerencias:")
        print("1. Verifica tu conexión a internet")
        print(f"2. Asegúrate de que el ticker '{ticker}' sea válido")
        print("3. Tickers disponibles: INTC, AMZN, ORCL, NVDA, MELI")
        print("4. Si el problema persiste, puedes cambiar el intervalo a '15m' o '1h'")
        import traceback
        traceback.print_exc()