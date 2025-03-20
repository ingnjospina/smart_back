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
                <body>
                    <h1 style="color: red;">⚠️ Alerta Crítica Detectada</h1>
                    <p><strong>Interruptor:</strong> {id_interruptor.nombre}</p>
                    <p><strong>Condición:</strong> {alerta['mensaje_condicion']}</p>
                    <p><strong>Recomendación:</strong> {alerta['recomendacion']}</p>
                    <p><strong>Tipo de Alerta:</strong> {alerta['color_alerta']}</p>
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
