import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime


class AlertaInterruptorEmail:
    @staticmethod
    def generar_alerta_interruptor(I_M, id_interruptor):
        send_message = False

        # Diccionario de colores HTML según la alerta
        color_alerta_html = {
            "Azul": "#0000FF",
            "Verde": "#008000",
            "Amarillo": "#FFA500",
            "Naranja": "#FF8C00",
            "Rojo": "#FF0000"
        }

        # Determinar la alerta según el valor de I_M
        if 86 <= I_M <= 100:
            alerta = {
                "mensaje_condicion": "Muy Bueno",
                "recomendacion": "Continuo mantenimiento normal.",
                "color_alerta": "Azul"
            }
        elif 71 <= I_M <= 85:
            alerta = {
                "mensaje_condicion": "Bueno",
                "recomendacion": "Continuo mantenimiento normal.",
                "color_alerta": "Verde"
            }
        elif 51 <= I_M <= 70:
            send_message = True  # Se envía alerta
            alerta = {
                "mensaje_condicion": "Regular",
                "recomendacion": "Generar alerta amarilla para incremento de pruebas de rutina.",
                "color_alerta": "Amarillo"
            }
        elif 31 <= I_M <= 50:
            send_message = True  # Se envía alerta
            alerta = {
                "mensaje_condicion": "Pobre",
                "recomendacion": "Generar alerta naranja para aumentar pruebas de rutina y programar posible cambio.",
                "color_alerta": "Naranja"
            }
        elif 0 <= I_M <= 30:
            send_message = True  # Se envía alerta
            alerta = {
                "mensaje_condicion": "Muy Pobre",
                "recomendacion": "Generar alerta roja para programar cambio lo antes posible.",
                "color_alerta": "Rojo"
            }
        else:
            alerta = {
                "mensaje_condicion": "Valor fuera de rango",
                "recomendacion": "Revisar la medición.",
                "color_alerta": "negro"
            }

        # Obtener la fecha y hora actual de la medición
        fecha_medicion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Obtener el color correspondiente
        color_texto = color_alerta_html.get(alerta["color_alerta"], "#000000")  # Negro por defecto

        # Enviar email si es una alerta (I_M <= 70)
        if send_message:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = os.getenv('SMTP_PORT')
            sender_email = os.getenv('SENDER_EMAIL')
            password = os.getenv('PASSWORD_EMAIL')
            receiver_email = os.getenv('FROM_EMAIL')

            # Generar el cuerpo del email en HTML con color dinámico
            html_body = f"""
            <html>
            <head>
                <style>
                    body {{
                        background-color: #ffffff;
                        font-family: Arial, sans-serif;
                        text-align: center;
                        margin: 0;
                        padding: 0;
                    }}
                    .container {{
                        width: 100%;
                        display: flex;
                        justify-content: center;
                        align-items: center;
                        min-height: 100vh;
                    }}
                    .alert-box {{
                        background-color: #f8f8f8;
                        border-radius: 10px;
                        box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.2);
                        padding: 20px;
                        width: 60%;
                        max-width: 500px;
                        text-align: left;
                    }}
                    h1 {{
                        color: red;
                        font-size: 24px;
                        text-align: center;
                    }}
                    p {{
                        font-size: 16px;
                        color: #333;
                        margin: 8px 0;
                    }}
                    .highlight {{
                        font-weight: bold;
                    }}
                    .alert-color {{
                        color: {color_texto}; /* Color dinámico según la alerta */
                        font-weight: bold;
                    }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="alert-box">
                        <h1>⚠️ Alerta Detectada</h1>
                        <p><span class="highlight">Interruptor:</span> {id_interruptor.nombre}</p>
                        <p><span class="highlight">Valor de Medición:</span> <span class="alert-color">{I_M:.2f}</span></p>
                        <p><span class="highlight">Fecha de Medición:</span> {fecha_medicion}</p>
                        <p><span class="highlight">Condición:</span> <span class="alert-color">{alerta['mensaje_condicion']}</span></p>
                        <p><span class="highlight">Recomendación:</span> {alerta['recomendacion']}</p>
                        <p><span class="highlight">Tipo de Alerta:</span> <span class="alert-color">{alerta['color_alerta'].capitalize()}</span></p>
                    </div>
                </div>
            </body>
            </html>
            """

            if os.getenv('ENABLE_MAILHOG', 'False') == 'True':
                print("Enviando email con MailHog...")

                send_mail(
                    f"🚨 Alerta en Interruptor {id_interruptor.nombre}",
                    "",  # Cuerpo de texto vacío (se enviará en HTML)
                    settings.DEFAULT_FROM_EMAIL,
                    ["test@example.com"],  # Destinatarios de prueba
                    fail_silently=False,
                    html_message=html_body,  # Envío en formato HTML
                )

            else:
                print("Enviando email con SMTP real...")

                message = MIMEMultipart()
                message["From"] = sender_email
                message["To"] = receiver_email
                message["Subject"] = f"🚨 Alerta en Interruptor {id_interruptor.nombre}"
                message.attach(MIMEText(html_body, "html"))

                server = None
                try:
                    server = smtplib.SMTP(smtp_server, smtp_port)
                    server.starttls()
                    server.login(sender_email, password)
                    server.sendmail(sender_email, receiver_email, message.as_string())
                    print("✅ Correo de alerta enviado con éxito")
                except Exception as e:
                    print(f"❌ Error al enviar el correo: {e}")
                finally:
                    if server:
                        server.quit()

        return alerta
