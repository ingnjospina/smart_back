import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime


class AlertaTransformadorEmail:
    @staticmethod
    def enviar_pronostico_transformador(pronostico_data, transformador_nombre, usuario_email, usuario_nombre=None):
        """
        Envía un correo electrónico con la información del pronóstico de un transformador.

        Args:
            pronostico_data: Diccionario con los datos del pronóstico
            transformador_nombre: Nombre del transformador
            usuario_email: Email del usuario destinatario
            usuario_nombre: Nombre del usuario (opcional)

        Returns:
            dict: Resultado del envío con éxito o error
        """

        # Diccionario de colores HTML según la alerta
        color_alerta_html = {
            "azul": "#007bff",
            "verde": "#28a745",
            "amarillo": "#ffc107",
            "naranja": "#fd7e14",
            "rojo": "#dc3545"
        }

        # Obtener el color correspondiente
        color_alerta = pronostico_data.get('color_alerta', '').lower()
        color_texto = color_alerta_html.get(color_alerta, "#6c757d")

        # Obtener la fecha actual
        fecha_envio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Generar el cuerpo del email en HTML
        html_body = f"""
        <html>
        <head>
            <style>
                body {{
                    background-color: #f0f0f5;
                    font-family: 'Arial', sans-serif;
                    padding: 0;
                    margin: 0;
                }}
                .container {{
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    padding: 20px;
                    background-color: #f0f0f5;
                }}
                .alert-box {{
                    background-color: white;
                    border-radius: 12px;
                    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
                    padding: 30px;
                    max-width: 600px;
                    width: 100%;
                    margin: auto;
                    border-top: 6px solid {color_texto};
                }}
                h1 {{
                    color: #333;
                    font-size: 24px;
                    text-align: center;
                    margin-bottom: 20px;
                }}
                p {{
                    font-size: 16px;
                    color: #333;
                    line-height: 1.6;
                    margin: 8px 0;
                }}
                .highlight {{
                    font-weight: bold;
                    color: #000;
                }}
                .alert-color {{
                    color: {color_texto};
                    font-weight: bold;
                }}
                .section {{
                    margin: 15px 0;
                    padding: 15px;
                    background-color: #f8f9fa;
                    border-radius: 8px;
                }}
                .section-title {{
                    font-weight: bold;
                    color: #495057;
                    margin-bottom: 10px;
                    font-size: 14px;
                    text-transform: uppercase;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert-box">
                    <h1>Pronostico de Transformador</h1>
                    {f'<p>Estimado(a) <strong>{usuario_nombre}</strong>,</p>' if usuario_nombre else ''}
                    <p>A continuacion se presenta la informacion del pronostico solicitado:</p>
                    <hr style="margin: 15px 0;">

                    <div class="section">
                        <div class="section-title">Informacion General</div>
                        <p><span class="highlight">Transformador:</span> {transformador_nombre}</p>
                        <p><span class="highlight">ID Pronostico:</span> {pronostico_data.get('idpronostico_transformador', 'N/A')}</p>
                        <p><span class="highlight">Fecha de Creacion:</span> {pronostico_data.get('fecha_creacion', 'N/A')}</p>
                    </div>

                    <div class="section">
                        <div class="section-title">Indices de Salud</div>
                        <p><span class="highlight">HI Total:</span> {pronostico_data.get('hi_total', 'N/A')}</p>
                        <p><span class="highlight">HI Funcional:</span> {pronostico_data.get('hi_funcional', 'N/A')}</p>
                        <p><span class="highlight">HI Dielectrico:</span> {pronostico_data.get('hi_dielectrico', 'N/A')}</p>
                        <p><span class="highlight">Condicion:</span> <span class="alert-color">{pronostico_data.get('condicion_hi', 'N/A')}</span></p>
                    </div>

                    <div class="section">
                        <div class="section-title">Mantenimiento</div>
                        <p><span class="highlight">RM Actual:</span> {pronostico_data.get('rm_actual', 'N/A')}</p>
                        <p><span class="highlight">Fecha Ultimo Mantenimiento:</span> {pronostico_data.get('fecha_ultimo_mantenimiento', 'N/A')}</p>
                        <p><span class="highlight">Fecha Programada:</span> {pronostico_data.get('fecha_programada', 'N/A')}</p>
                        <p><span class="highlight">Fecha Optima Sugerida:</span> {pronostico_data.get('fecha_optima_sugerida', 'N/A')}</p>
                    </div>

                    <div class="section">
                        <div class="section-title">Alerta y Recomendacion</div>
                        <p><span class="highlight">Tipo de Alerta:</span> <span class="alert-color">{pronostico_data.get('color_alerta', 'N/A').capitalize()}</span></p>
                        <p><span class="highlight">Recomendacion:</span> {pronostico_data.get('recomendacion', 'N/A')}</p>
                    </div>

                    <hr style="margin: 15px 0;">
                    <p style="font-size: 12px; color: #6c757d; text-align: center;">
                        Este correo fue enviado el {fecha_envio} desde el sistema SMART.
                    </p>
                </div>
            </div>
        </body>
        </html>
        """

        smtp_server = os.getenv('SMTP_SERVER')
        smtp_port = os.getenv('SMTP_PORT')
        sender_email = os.getenv('SENDER_EMAIL')
        password = os.getenv('PASSWORD_EMAIL')

        subject = f"Pronostico Transformador: {transformador_nombre}"

        if os.getenv('ENABLE_MAILHOG', 'False') == 'True':
            try:
                send_mail(
                    subject,
                    "",
                    settings.DEFAULT_FROM_EMAIL,
                    [usuario_email],
                    fail_silently=False,
                    html_message=html_body,
                )
                return {"success": True, "message": "Correo enviado exitosamente"}
            except Exception as e:
                return {"success": False, "message": f"Error al enviar el correo: {str(e)}"}
        else:
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = usuario_email
            message["Subject"] = subject
            message.attach(MIMEText(html_body, "html"))

            server = None
            try:
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, usuario_email, message.as_string())
                return {"success": True, "message": "Correo enviado exitosamente"}
            except Exception as e:
                return {"success": False, "message": f"Error al enviar el correo: {str(e)}"}
            finally:
                if server:
                    server.quit()
