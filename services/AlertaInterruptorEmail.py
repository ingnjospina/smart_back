import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import send_mail
from django.conf import settings


class AlertaInterruptorEmail:
    @staticmethod
    def generar_alerta_interruptor(I_M, id_interruptor):
        send_message = False

        # Determinar la alerta según I_M
        if I_M > 1.5:
            send_message = True
            alerta = {
                "mensaje_condicion": "Crítico",
                "recomendacion": "Se recomienda mantenimiento inmediato.",
                "color_alerta": "Rojo",
            }

        elif 1.0 <= I_M <= 1.5:
            alerta = {
                "mensaje_condicion": "Precaución",
                "recomendacion": "Monitoreo frecuente recomendado.",
                "color_alerta": "Amarillo",
            }

        else:
            alerta = {
                "mensaje_condicion": "Normal",
                "recomendacion": "No se requiere mantenimiento inmediato.",
                "color_alerta": "Verde",
            }

        # Enviar email si la alerta es roja
        if send_message:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = os.getenv('SMTP_PORT')
            sender_email = os.getenv('SENDER_EMAIL')
            password = os.getenv('PASSWORD_EMAIL')
            receiver_email = os.getenv('FROM_EMAIL')

            # Generar el cuerpo del email en HTML
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
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="alert-box">
                        <h1>⚠️ Alerta Crítica Detectada</h1>
                        <p><span class="highlight">Interruptor:</span> {id_interruptor.nombre}</p>
                        <p><span class="highlight">Condición:</span> {alerta['mensaje_condicion']}</p>
                        <p><span class="highlight">Recomendación:</span> {alerta['recomendacion']}</p>
                        <p><span class="highlight">Tipo de Alerta:</span> {alerta['color_alerta']}</p>
                    </div>
                </div>
            </body>
            </html>
            """

            if os.getenv('ENABLE_MAILHOG', 'False') == 'True':
                print("Enviando email con MailHog...")

                send_mail(
                    f"🚨 Alerta Crítica en Interruptor {id_interruptor.nombre}",
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
                message["Subject"] = f"🚨 Alerta Crítica en Interruptor {id_interruptor.nombre}"
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
