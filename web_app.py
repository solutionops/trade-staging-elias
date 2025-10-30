from flask import Flask, render_template_string, jsonify, send_file, request
import json
import os
import subprocess

app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Trading Prediction</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            overflow: hidden;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            text-align: center;
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .header p {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .content {
            padding: 40px;
        }
        
        .controls {
            display: flex;
            gap: 15px;
            justify-content: center;
            flex-wrap: wrap;
            margin-bottom: 30px;
        }
        
        select, button {
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 1em;
            border: none;
            cursor: pointer;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);
        }
        
        select {
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            font-weight: bold;
        }
        
        button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.6);
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            padding: 25px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
        }
        
        .stat-card h3 {
            color: #667eea;
            font-size: 0.9em;
            text-transform: uppercase;
            letter-spacing: 1px;
            margin-bottom: 10px;
        }
        
        .stat-card .value {
            font-size: 2em;
            font-weight: bold;
            color: #333;
        }
        
        .prediction-dates {
            background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
        }
        
        .date-info {
            text-align: center;
        }
        
        .date-info h3 {
            color: #2d5a3d;
            font-size: 1.1em;
            margin-bottom: 10px;
        }
        
        .date-info .date-value {
            font-size: 1.3em;
            font-weight: bold;
            color: #1a3d27;
        }
        
        .chart-container {
            background: #f8f9fa;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }
        
        .chart-container img {
            width: 100%;
            height: auto;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        .date-picker-container {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
            text-align: center;
        }
        
        .date-picker-container h3 {
            color: white;
            font-size: 1.5em;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }
        
        .date-picker-input {
            padding: 12px 20px;
            border-radius: 10px;
            border: none;
            font-size: 1.1em;
            margin-right: 15px;
            box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        }
        
        .date-picker-button {
            padding: 12px 30px;
            background: white;
            color: #f5576c;
            border: none;
            border-radius: 10px;
            font-size: 1em;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.3s ease;
        }
        
        .date-picker-button:hover {
            transform: translateY(-2px);
        }
        
        .predicted-price-result {
            margin-top: 20px;
            font-size: 1.5em;
            font-weight: bold;
            color: white;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            line-height: 1.8;
        }
        
        .predicted-price-result small {
            display: block;
            margin-top: 10px;
            font-size: 0.7em;
            opacity: 0.9;
        }
        
        .loading {
            text-align: center;
            padding: 60px;
            font-size: 1.5em;
            color: #667eea;
        }
        
        .error {
            background: #fee;
            color: #c33;
            padding: 20px;
            border-radius: 10px;
            margin: 20px;
            text-align: center;
        }
        
        .success {
            background: #efe;
            color: #3c3;
            padding: 15px;
            border-radius: 10px;
            margin-bottom: 20px;
            text-align: center;
            display: none;
        }
        
        @media (max-width: 768px) {
            .header h1 {
                font-size: 1.8em;
            }
            
            .content {
                padding: 20px;
            }
            
            .stats {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📈 Trading Prediction System</h1>
            <p id="subtitle">Análisis con Regresión Polinomial</p>
        </div>
        
        <div class="content">
            <div class="success" id="successMessage">
                ✓ Datos actualizados correctamente
            </div>
            
            <div class="controls">
                <select id="tickerSelect">
                    <option value="INTC">Intel (INTC)</option>
                    <option value="AMZN">Amazon (AMZN)</option>
                    <option value="ORCL">Oracle (ORCL)</option>
                    <option value="NVDA">NVIDIA (NVDA)</option>
                    <option value="MELI">MercadoLibre (MELI)</option>
                </select>
                <button onclick="updateData()">🔄 Actualizar Datos</button>
                <button onclick="downloadExcel()">📥 Descargar Excel</button>
            </div>
            
            <div id="loading" class="loading">
                Cargando gráfico...
            </div>
            
            <div id="content" style="display: none;">
                <div class="prediction-dates" id="dates">
                    <!-- Las fechas se cargarán aquí -->
                </div>
                
                <div class="stats" id="stats">
                    <!-- Las estadísticas se cargarán aquí -->
                </div>
                
                <div class="chart-container">
                    <img id="chart" src="" alt="Gráfico de predicción">
                </div>
                
                <div class="date-picker-container">
                    <h3>🔍 Consultar Valor Proyectado para una Fecha Específica</h3>
                    <input type="date" id="datePicker" class="date-picker-input" 
                           min="" max="">
                    <button onclick="getPredictedPrice()" class="date-picker-button">Ver Proyección</button>
                    <div id="predictionResult" class="predicted-price-result"></div>
                </div>
            </div>
            
            <div id="error" class="error" style="display: none;">
                Error: No se encontraron datos de predicción. Por favor ejecuta getData.py primero.
            </div>
        </div>
    </div>
    
    <script>
        let currentTicker = 'INTC';
        
        function loadChart(ticker = null) {
            if (ticker) {
                currentTicker = ticker;
            }
            
            fetch('/api/data')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('error').style.display = 'none';
                    document.getElementById('content').style.display = 'block';
                    
                    // Actualizar título
                    document.getElementById('subtitle').textContent = 
                        `${data.ticker_name || 'Empresa'} (${data.ticker || 'N/A'})`;
                    
                    // Mostrar el gráfico
                    document.getElementById('chart').src = 'data:image/png;base64,' + data.image_base64;
                    
                    // Mostrar fechas de predicción
                    // Formatear fechas correctamente
                    const formatDate = (dateStr) => {
                        if (!dateStr) return 'N/A';
                        const date = new Date(dateStr);
                        if (isNaN(date.getTime())) return 'N/A';
                        return date.toLocaleString('es-ES', {
                            year: 'numeric',
                            month: 'short',
                            day: 'numeric',
                            hour: '2-digit',
                            minute: '2-digit'
                        });
                    };
                    
                    const datesHtml = `
                        <div class="date-info">
                            <h3>📅 Inicio de Predicción</h3>
                            <div class="date-value">${formatDate(data.prediction_start_date)}</div>
                        </div>
                        <div class="date-info">
                            <h3>📈 Precio Inicial Previsto</h3>
                            <div class="date-value">$${data.predicted_next_price.toFixed(2)}</div>
                        </div>
                        <div class="date-info">
                            <h3>📊 Precio Final Previsto</h3>
                            <div class="date-value">$${data.predicted_final_price.toFixed(2)}</div>
                        </div>
                        <div class="date-info">
                            <h3>🎯 Final de Predicción</h3>
                            <div class="date-value">${formatDate(data.prediction_end_date)}</div>
                        </div>
                    `;
                    document.getElementById('dates').innerHTML = datesHtml;
                    
                    // Mostrar estadísticas
                    const changePercent = ((data.predicted_final_price - data.last_price) / data.last_price * 100).toFixed(2);
                    const statsHtml = `
                        <div class="stat-card">
                            <h3>Precio Actual</h3>
                            <div class="value">$${data.last_price.toFixed(2)}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Puntos Históricos</h3>
                            <div class="value">${data.historical_points.toLocaleString()}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Puntos Predichos</h3>
                            <div class="value">${data.predicted_points.toLocaleString()}</div>
                        </div>
                        <div class="stat-card">
                            <h3>Precisión (R²)</h3>
                            <div class="value">${(data.r2_score * 100).toFixed(2)}%</div>
                        </div>
                        <div class="stat-card">
                            <h3>Variación Est. Final</h3>
                            <div class="value" style="color: ${parseFloat(changePercent) >= 0 ? '#4CAF50' : '#f44336'}">
                                ${changePercent > 0 ? '+' : ''}${changePercent}%
                            </div>
                        </div>
                    `;
                    document.getElementById('stats').innerHTML = statsHtml;
                    
                    // Configurar el date picker con los límites de predicción
                    const startDate = new Date(data.prediction_start_date);
                    const endDate = new Date(data.prediction_end_date);
                    
                    document.getElementById('datePicker').min = startDate.toISOString().slice(0, 10);
                    document.getElementById('datePicker').max = endDate.toISOString().slice(0, 10);
                    
                    // Almacenar datos de predicción globalmente
                    window.predictionData = data.prediction_data || [];
                })
                .catch(error => {
                    document.getElementById('loading').style.display = 'none';
                    document.getElementById('content').style.display = 'none';
                    document.getElementById('error').style.display = 'block';
                    console.error('Error:', error);
                });
        }
        
        function getPredictedPrice() {
            const selectedDate = document.getElementById('datePicker').value;
            const resultDiv = document.getElementById('predictionResult');
            
            if (!selectedDate) {
                resultDiv.innerHTML = '⚠️ Por favor selecciona una fecha';
                return;
            }
            
            if (!window.predictionData || window.predictionData.length === 0) {
                resultDiv.innerHTML = '⚠️ No hay datos de predicción disponibles';
                return;
            }
            
            // Buscar el valor más cercano a la fecha seleccionada
            const selectedTimestamp = new Date(selectedDate).getTime();
            
            let closestPrediction = null;
            let minDiff = Infinity;
            
            window.predictionData.forEach(pred => {
                const predTimestamp = new Date(pred.date).getTime();
                const diff = Math.abs(predTimestamp - selectedTimestamp);
                
                if (diff < minDiff) {
                    minDiff = diff;
                    closestPrediction = pred;
                }
            });
            
            if (closestPrediction) {
                const predDate = new Date(closestPrediction.date + 'T00:00:00');
                const close = closestPrediction.close.toFixed(2);
                const high = closestPrediction.high.toFixed(2);
                const low = closestPrediction.low.toFixed(2);
                const open = closestPrediction.open.toFixed(2);
                
                resultDiv.innerHTML = `
                    📊 ${predDate.toLocaleDateString('es-ES', {
                        year: 'numeric',
                        month: 'short',
                        day: 'numeric'
                    })}<br>
                    🔹 Apertura: $${open}<br>
                    🔺 Máximo: $${high}<br>
                    🔻 Mínimo: $${low}<br>
                    🔹 Cierre: $${close}<br>
                    <small style="font-size: 0.7em;">Rango diario: $${low} - $${high}</small>
                `;
            } else {
                resultDiv.innerHTML = '⚠️ No se encontró predicción para esa fecha';
            }
        }
        
        function updateData() {
            const ticker = document.getElementById('tickerSelect').value;
            document.getElementById('loading').style.display = 'block';
            document.getElementById('content').style.display = 'none';
            document.getElementById('successMessage').style.display = 'none';
            
            fetch('/api/update', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ ticker: ticker })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('successMessage').style.display = 'block';
                    setTimeout(() => {
                        loadChart(ticker);
                    }, 2000);
                } else {
                    alert('Error al actualizar datos: ' + data.error);
                    document.getElementById('loading').style.display = 'none';
                }
            })
            .catch(error => {
                alert('Error al actualizar datos');
                document.getElementById('loading').style.display = 'none';
            });
        }
        
        function downloadExcel() {
            window.location.href = '/download/excel';
        }
        
        // Cargar el gráfico al iniciar
        loadChart();
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data')
def get_data():
    try:
        if os.path.exists('model_prediction.json'):
            with open('model_prediction.json', 'r') as f:
                data = json.load(f)
            return jsonify(data)
        else:
            return jsonify({'error': 'Datos no encontrados. Ejecuta getData.py primero.'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/update', methods=['POST'])
def update_data():
    try:
        data = request.json
        ticker = data.get('ticker', 'INTC')
        
        # Ejecutar getData.py con el ticker seleccionado
        result = subprocess.run(
            ['python', 'getData.py', ticker],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        if result.returncode == 0:
            return jsonify({'success': True, 'message': 'Datos actualizados correctamente'})
        else:
            return jsonify({'success': False, 'error': result.stderr})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/download/excel')
def download_excel():
    if os.path.exists('stock_data.xlsx'):
        return send_file('stock_data.xlsx', as_attachment=True)
    else:
        return "Archivo Excel no encontrado", 404

if __name__ == '__main__':
    print("=" * 60)
    print("Servidor web iniciado")
    print("=" * 60)
    print("Accede a: http://127.0.0.1:8080")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=8080)