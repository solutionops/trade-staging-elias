import os
import json
import smtplib
import ssl
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd


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


def build_html_table(model_data: dict, last_close_excel: float, prev_close_excel: float) -> str:
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
    html.append(f"<p><b>Modelo:</b> {('Neural Network (MLP)' if model_type=='neuralnetwork' else 'Polynomial Regression')} | "
                f"<b>R²:</b> {r2_score:.4f if isinstance(r2_score, (float, int)) else 'N/D'}</p>")

    html.append("<table border=1 cellspacing=0 cellpadding=6 style='border-collapse:collapse;font-family:Arial,sans-serif'>")
    html.append("<thead><tr style='background:#f0f3f7'>"
                "<th>Concepto</th><th>Valor</th></tr></thead><tbody>")
    html.append(f"<tr><td>Precio actual (JSON)</td><td>{fmt(last_price)}</td></tr>")
    html.append(f"<tr><td>Precio de cierre (Excel) - Último</td><td>{fmt(last_close_excel)}</td></tr>")
    html.append(f"<tr><td>Precio de cierre (Excel) - Anterior</td><td>{fmt(prev_close_excel)}</td></tr>")
    html.append("</tbody></table><br>")

    # Tabla de proyecciones
    html.append("<h3>Proyecciones</h3>")
    html.append("<table border=1 cellspacing=0 cellpadding=6 style='border-collapse:collapse;font-family:Arial,sans-serif'>")
    html.append("<thead><tr style='background:#f0f3f7'>"
                "<th>Día</th><th>Apertura</th><th>Mínimo</th><th>Máximo</th><th>Cierre</th></tr></thead><tbody>")
    if next_day:
        html.append(f"<tr><td>Próximo ({fmt_date(next_day.get('date'))})</td>"
                    f"<td>{fmt(next_day.get('open'))}</td>"
                    f"<td>{fmt(next_day.get('low'))}</td>"
                    f"<td>{fmt(next_day.get('high'))}</td>"
                    f"<td>{fmt(next_day.get('close'))}</td></tr>")
    if final_day and final_day is not next_day:
        html.append(f"<tr><td>Final ({fmt_date(final_day.get('date'))})</td>"
                    f"<td>{fmt(final_day.get('open'))}</td>"
                    f"<td>{fmt(final_day.get('low'))}</td>"
                    f"<td>{fmt(final_day.get('high'))}</td>"
                    f"<td>{fmt(final_day.get('close'))}</td></tr>")
    html.append("</tbody></table>")

    return "\n".join(html)


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
    prediction_path = os.path.join(data_dir, 'model_prediction.json')
    excel_path = os.path.join(data_dir, 'stock_data.xlsx')

    model_data = load_prediction(prediction_path)
    last_close_excel, prev_close_excel = load_last_prices(excel_path)

    html_body = build_html_table(model_data, last_close_excel, prev_close_excel)
    ticker = model_data.get('ticker', 'N/A')
    now_local = datetime.now().strftime('%Y-%m-%d %H:%M')
    subject = f"Proyección {ticker} - {now_local}"

    send_email(subject, html_body)
    print("Correo enviado correctamente")


if __name__ == '__main__':
    try:
        main()
    except Exception as e:
        print(f"Error enviando correo: {e}")

