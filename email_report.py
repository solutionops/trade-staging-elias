import os
import json
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import subprocess


def load_prediction(path: str) -> dict:
    if not os.path.exists(path):
        raise FileNotFoundError(f"No se encontró el archivo de predicción: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_last_prices(excel_path: str) -> tuple[float, float]:
    if not os.path.exists(excel_path):
        # Si no existe, devolvemos valores desconocidos
        return float('nan'), float('nan')
    df = pd.read_excel(excel_path)
    if 'Close' not in df.columns or len(df.index) < 2:
        return float('nan'), float('nan')
    last_close = float(df['Close'].iloc[-1])
    prev_close = float(df['Close'].iloc[-2])
    return last_close, prev_close


def build_html_table(model_data: dict, last_close_excel: float, prev_close_excel: float, days_ahead: int = 5) -> str:
    ticker = model_data.get('ticker', 'N/A')
    ticker_name = model_data.get('ticker_name', ticker)
    model_type = model_data.get('model_type', 'polynomial')
    r2_score = model_data.get('r2_score', None)

    last_price = model_data.get('last_price', float('nan'))
    prediction_data = model_data.get('prediction_data', [])

    # Próximo día proyectado (si existe)
    next_day = prediction_data[0] if prediction_data else None
    final_day = prediction_data[-1] if prediction_data else None

    def fmt(v):
        try:
            return f"${float(v):.2f}"
        except Exception:
            return "N/D"

    def fmt_date(d):
        try:
            return datetime.fromisoformat((d or '').split('T')[0]).strftime('%Y-%m-%d')
        except Exception:
            return d or 'N/D'

    html = []
    html.append(f"<h2>Reporte de Proyección - {ticker_name} ({ticker})</h2>")
    r2_display = f"{r2_score:.4f}" if isinstance(r2_score, (float, int)) else "N/D"
    html.append(f"<p><b>Modelo:</b> {('Neural Network (MLP)' if model_type=='neuralnetwork' else 'Polynomial Regression')} | "
                f"<b>R²:</b> {r2_display}</p>")

    html.append("<table border=1 cellspacing=0 cellpadding=6 style='border-collapse:collapse;font-family:Arial,sans-serif'>")
    html.append("<thead><tr style='background:#f0f3f7'>"
                "<th>Concepto</th><th>Valor</th></tr></thead><tbody>")
    html.append(f"<tr><td>Precio actual (JSON)</td><td>{fmt(last_price)}</td></tr>")
    html.append(f"<tr><td>Precio de cierre (Excel) - Último</td><td>{fmt(last_close_excel)}</td></tr>")
    html.append(f"<tr><td>Precio de cierre (Excel) - Anterior</td><td>{fmt(prev_close_excel)}</td></tr>")
    html.append("</tbody></table><br>")

    # Tabla de proyecciones
    html.append("<h3>Proyecciones (próximos días)</h3>")
    html.append("<table border=1 cellspacing=0 cellpadding=6 style='border-collapse:collapse;font-family:Arial,sans-serif'>")
    html.append("<thead><tr style='background:#f0f3f7'>"
                "<th>Día</th><th>Apertura</th><th>Mínimo</th><th>Máximo</th><th>Cierre</th></tr></thead><tbody>")
    # Listado de los próximos N días (por defecto 5)
    for entry in prediction_data[:max(0, days_ahead)]:
        html.append(
            f"<tr><td>{fmt_date(entry.get('date'))}</td>"
            f"<td>{fmt(entry.get('open'))}</td>"
            f"<td>{fmt(entry.get('low'))}</td>"
            f"<td>{fmt(entry.get('high'))}</td>"
            f"<td>{fmt(entry.get('close'))}</td></tr>"
        )
    html.append("</tbody></table>")

    return "\n".join(html)


def build_model_section(title: str, model_data: dict, last_close_excel: float, prev_close_excel: float, days_ahead: int = 5) -> str:
    section = [f"<h3 style='margin-top:18px'>{title}</h3>"]
    section.append(build_html_table(model_data, last_close_excel, prev_close_excel, days_ahead))
    return "\n".join(section)


def send_email(subject: str, html_body: str) -> None:
    smtp_host = os.getenv('SMTP_HOST', '')
    smtp_port = int(os.getenv('SMTP_PORT', '0') or '0')
    smtp_user = os.getenv('SMTP_USER', '')
    smtp_pass = os.getenv('SMTP_PASS', '')
    to_emails = os.getenv('SMTP_TO', '')
    from_email = os.getenv('SMTP_FROM', smtp_user)

    if not (smtp_host and smtp_port and smtp_user and smtp_pass and to_emails):
        raise RuntimeError("Credenciales SMTP incompletas. Define SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASS, SMTP_TO")

    recipients = [e.strip() for e in to_emails.split(',') if e.strip()]
    if not recipients:
        raise RuntimeError("SMTP_TO no contiene destinatarios válidos")

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_email
    msg['To'] = ", ".join(recipients)
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))

    if smtp_port == 465:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, recipients, msg.as_string())
    else:
        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.ehlo()
            try:
                server.starttls(context=ssl.create_default_context())
                server.ehlo()
            except smtplib.SMTPException:
                pass
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, recipients, msg.as_string())


def main():
    data_dir = os.getenv('DATA_DIR', 'data')
    excel_path = os.path.join(data_dir, 'stock_data.xlsx')
    model_type = os.getenv('MODEL_TYPE', 'polynomial').lower()
    # Tickers por defecto: INTC, ORCL, NVDA, AMZN
    tickers_env = os.getenv('TICKERS', 'INTC,ORCL,NVDA,AMZN')
    tickers = [t.strip().upper() for t in tickers_env.split(',') if t.strip()]

    sections: list[str] = []
    used_tickers: list[str] = []

    for ticker in tickers:
        # Sección por ticker con ambos modelos
        per_ticker_sections: list[str] = [f"<h2 style='margin-top:24px'>Ticker: {ticker}</h2>"]
        last_close_excel, prev_close_excel = load_last_prices(excel_path)
        prediction_path = os.path.join(data_dir, 'model_prediction.json')

        for model_type in ("polynomial", "neuralnetwork"):
            try:
                subprocess.run(
                    ['python', 'getData.py', ticker, model_type],
                    cwd=os.path.dirname(os.path.abspath(__file__)),
                    check=True
                )
            except subprocess.CalledProcessError as e:
                per_ticker_sections.append(f"<p><b>{model_type}:</b> Error al generar predicción ({e})</p>")
                continue

            try:
                model_data = load_prediction(prediction_path)
            except Exception as e:
                per_ticker_sections.append(f"<p><b>{model_type}:</b> No se pudo leer la predicción ({e})</p>")
                continue

            title = "Modelo: Polynomial Regression" if model_type == "polynomial" else "Modelo: Neural Network (MLP)"
            per_ticker_sections.append(
                build_model_section(title, model_data, last_close_excel, prev_close_excel, days_ahead=5)
            )

        if len(per_ticker_sections) > 1:
            sections.append("<div>" + "\n".join(per_ticker_sections) + "</div>")
            used_tickers.append(ticker)

    # Armar correo final
    now_local = datetime.now().strftime('%Y-%m-%d %H:%M')
    subject = f"Proyecciones ({', '.join(used_tickers)}) - {now_local}" if used_tickers else f"Proyecciones - {now_local}"
    html_body = "<br><hr><br>".join(sections) if sections else "<p>No fue posible generar el reporte.</p>"

    send_email(subject, html_body)
    print("Correo enviado correctamente")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error enviando correo: {e}")

