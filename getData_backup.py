import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from sklearn.preprocessing import PolynomialFeatures
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline
import json
import base64
from io import BytesIO

def get_stock_data(ticker="INTC", interval="1h", days=90):
    """
    Obtiene datos históricos de una acción en intervalos específicos
    desde hace N días hasta hoy (máximo 60 días para 5m, 730 días para 1h)
    """
    end_date = datetime.now()
    # Límites según intervalo
    if interval == "5m":
        max_days = 60
    elif interval in ["15m", "30m"]:
        max_days = 60
    elif interval in ["1h"]:
        max_days = 730  # ~2 años
    elif interval in ["1d"]:
        max_days = None  # Sin límite práctico
    else:
        max_days = 60
    
    start_date = end_date - timedelta(days=min(days, max_days) if max_days else days)
    
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

def train_polynomial_model(data, degree=3):
    """
    Entrena un modelo de regresión polinomial con los datos históricos
    """
X = np.arange(len(data)).reshape(-1, 1)
y = data['Close'].values

    # Crear pipeline con transformación polinomial y regresión lineal
    model = Pipeline([
        ('poly', PolynomialFeatures(degree=degree)),
        ('linear', LinearRegression())
    ])
    
model.fit(X, y)
y_pred = model.predict(X)

    print(f"Modelo entrenado con grado polinomial: {degree}")
    print(f"R² Score: {model.score(X, y):.4f}")
    
    return model, X, y, y_pred

def predict_next_month(model, historical_length, interval="1h"):
    """
    Predice el comportamiento del próximo mes basado en el modelo entrenado
    """
    # Calcular puntos de predicción según el intervalo
    if interval == "1h":
        # Para 1 hora: 20 días de trading * 6.5 horas por día = 130 puntos
        next_month_points = 20 * 6.5
    elif interval == "5m":
        # Para 5 minutos: 20 días * 6.5 horas * 12 intervalos = 1,560 puntos
        next_month_points = 20 * 6.5 * 12
    elif interval == "15m":
        # Para 15 minutos: 20 días * 6.5 horas * 4 intervalos = 520 puntos
        next_month_points = 20 * 6.5 * 4
    elif interval == "1d":
        # Para 1 día: 20 días de trading
        next_month_points = 20
    else:
        # Default para otros intervalos (asumiendo horario de trading)
        next_month_points = 20 * 6.5 * 12
    
    X_future = np.arange(historical_length, historical_length + next_month_points).reshape(-1, 1)
    y_future = model.predict(X_future)
    
    print(f"Predicción generada para {next_month_points} puntos del próximo mes")
    
    return X_future, y_future

def generate_future_dates(start_date, num_intervals, freq="1H"):
    """
    Genera fechas futuras para la predicción según el intervalo
    """
    if freq == "1h" or freq == "1H":
        end_date = start_date + timedelta(hours=num_intervals)
    elif freq == "5min":
        end_date = start_date + timedelta(minutes=5 * num_intervals)
    elif freq == "15min":
        end_date = start_date + timedelta(minutes=15 * num_intervals)
    else:
        end_date = start_date + timedelta(hours=num_intervals)
    
    return pd.date_range(start=start_date, end=end_date, freq=freq)[:num_intervals]

def create_plot(data, y_pred, future_dates, y_future, ticker="INTC"):
    """
    Crea un gráfico con los datos históricos, el ajuste del modelo y las predicciones futuras
    """
    plt.figure(figsize=(20, 10))
    
    # Datos históricos reales
    plt.plot(data.index, data['Close'].values, label='Precio Real Histórico', 
             linewidth=2, color='blue', alpha=0.7)
    
    # Ajuste del modelo
    plt.plot(data.index, y_pred, label='Modelo (Regresión Polinomial)', 
             linewidth=2, color='red', linestyle='--', alpha=0.8)
    
    # Predicciones futuras
    plt.plot(future_dates, y_future, label='Predicción Próximo Mes', 
             linewidth=2, color='green', alpha=0.8)
    
    # Línea vertical separando histórico de predicción
    plt.axvline(x=data.index[-1], color='gray', linestyle=':', linewidth=2, label='Hoy', alpha=0.6)
    
    # Agregar fechas y precios en puntos clave de la predicción futura
    if len(future_dates) > 0 and len(y_future) > 0:
        # Convertir a valores escalares si son arrays numpy
        y_start = float(y_future[0]) if hasattr(y_future[0], 'item') else y_future[0]
        y_end = float(y_future[-1]) if hasattr(y_future[-1], 'item') else y_future[-1]
        
        # Marcar inicio de predicción
        plt.annotate(f'Inicio\n{future_dates[0].strftime("%d/%m %H:%M")}\n${y_start:.2f}',
                    xy=(future_dates[0], y_start), 
                    xytext=(10, 30), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='green', alpha=0.7),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                    fontsize=9, fontweight='bold', color='white')
        
        # Marcar punto medio de predicción (si hay suficientes datos)
        if len(future_dates) > 10:
            mid_point = len(future_dates) // 2
            y_mid = float(y_future[mid_point]) if hasattr(y_future[mid_point], 'item') else y_future[mid_point]
            plt.annotate(f'{future_dates[mid_point].strftime("%d/%m %H:%M")}\n${y_mid:.2f}',
                        xy=(future_dates[mid_point], y_mid), 
                        xytext=(10, -40), textcoords='offset points',
                        bbox=dict(boxstyle='round,pad=0.5', fc='orange', alpha=0.7),
                        arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                        fontsize=9, fontweight='bold', color='white')
        
        # Marcar final de predicción
        plt.annotate(f'Final\n{future_dates[-1].strftime("%d/%m %H:%M")}\n${y_end:.2f}',
                    xy=(future_dates[-1], y_end), 
                    xytext=(-50, 30), textcoords='offset points',
                    bbox=dict(boxstyle='round,pad=0.5', fc='darkgreen', alpha=0.8),
                    arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0'),
                    fontsize=9, fontweight='bold', color='white')
    
    plt.xlabel('Fecha', fontsize=12, fontweight='bold')
    plt.ylabel('Precio (USD)', fontsize=12, fontweight='bold')
    plt.title(f'{ticker} - Análisis con Regresión Polinomial y Predicción del Próximo Mes\nIntervalo: 1 hora', 
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
    data = get_stock_data(ticker=ticker, interval="1h", days=90)  # 3 meses en intervalos de 1 hora
    
    # 2. Guardar en Excel
    print("\n" + "=" * 60)
    print("PASO 2: Guardando datos en Excel")
    print("=" * 60)
    save_to_excel(data, "stock_data.xlsx")
    
    # 3. Entrenar modelo
    print("\n" + "=" * 60)
    print("PASO 3: Entrenando modelo de regresión polinomial")
    print("=" * 60)
    model, X, y, y_pred = train_polynomial_model(data, degree=3)
    
    # 4. Predecir próximo mes
    print("\n" + "=" * 60)
    print("PASO 4: Generando predicción del próximo mes")
    print("=" * 60)
    interval = "1h"  # Intervalo usado
    X_future, y_future = predict_next_month(model, len(data), interval=interval)
    
    # Generar fechas futuras según el intervalo
    if interval == "1h":
        freq = "1h"  # Usar formato estándar de pandas
    elif interval == "5m":
        freq = "5min"
    elif interval == "15m":
        freq = "15min"
    else:
        freq = "1h"
    
    future_dates = generate_future_dates(data.index[-1], len(y_future), freq=freq)
    
    # 5. Crear gráfico
    print("\n" + "=" * 60)
    print("PASO 5: Generando gráfico")
    print("=" * 60)
    image_base64 = create_plot(data, y_pred, future_dates, y_future, ticker=ticker)
    
    # 6. Guardar información del modelo para la web
    # Convertir arrays numpy a valores escalares correctamente
    if isinstance(y_future, np.ndarray):
        pred_next = float(y_future.item(0)) if y_future.size > 0 else 0.0
        pred_final = float(y_future.item(-1)) if y_future.size > 0 else 0.0
    else:
        pred_next = float(y_future[0]) if len(y_future) > 0 else 0.0
        pred_final = float(y_future[-1]) if len(y_future) > 0 else 0.0
    
    model_data = {
        'image_base64': image_base64,
        'historical_points': len(data),
        'predicted_points': len(y_future),
        'last_price': float(data['Close'].iloc[-1]),
        'predicted_next_price': pred_next,
        'predicted_final_price': pred_final,
        'r2_score': float(model.score(X, y)),
        'ticker': ticker,
        'ticker_name': get_ticker_name(ticker),
        'prediction_start_date': future_dates[0].strftime('%Y-%m-%d %H:%M:%S') if len(future_dates) > 0 else '',
        'prediction_end_date': future_dates[-1].strftime('%Y-%m-%d %H:%M:%S') if len(future_dates) > 0 else ''
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