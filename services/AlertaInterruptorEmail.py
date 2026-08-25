import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime


class AlertaInterruptorEmail:
    @staticmethod
    def generar_alerta_interruptor(I_M, id_interruptor, usuario_email=None, usuario_nombre=None):
        send_message = False

        # I_M llega normalizado en escala 0-1; los rangos de condición
        # están definidos en porcentaje (%IM), por eso se escala aquí.
        I_M = float(I_M) * 100

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
            try:
                smtp_server = os.getenv('SMTP_SERVER')
                smtp_port = os.getenv('SMTP_PORT')
                sender_email = os.getenv('SENDER_EMAIL')
                password = os.getenv('PASSWORD_EMAIL')
                receiver_email = usuario_email if usuario_email else os.getenv('FROM_EMAIL')

                html_body = f"""
                <html>
                <head>
                    <style>
                        body {{ background-color: #f0f0f5; font-family: 'Arial', sans-serif; padding: 0; margin: 0; }}
                        .container {{ display: flex; justify-content: center; align-items: center; padding: 20px; background-color: #f0f0f5; }}
                        .alert-box {{ background-color: white; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.1); padding: 30px; max-width: 600px; width: 100%; margin: auto; border-top: 6px solid {color_texto}; }}
                        h1 {{ color: #D32F2F; font-size: 28px; text-align: center; margin-bottom: 20px; }}
                        p {{ font-size: 16px; color: #333; line-height: 1.6; margin: 8px 0; }}
                        .highlight {{ font-weight: bold; color: #000; }}
                        .alert-color {{ color: {color_texto}; font-weight: bold; }}
                    </style>
                </head>
                <body>
                    <div class="container">
                        <div class="alert-box">
                            <h1>⚠️ Alerta Detectada</h1>
                            {f'<p>Estimado(a) <strong>{usuario_nombre}</strong>,</p>' if usuario_nombre else ''}
                            <p>Se ha detectado una alerta en el siguiente interruptor:</p>
                            <hr style="margin: 15px 0;">
                            <p><span class="highlight">Interruptor:</span> {id_interruptor.nombre}</p>
                            <p><span class="highlight">Valor de Medición:</span> <span class="alert-color">{I_M:.2f}%</span></p>
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
                    send_mail(
                        f"🚨 Alerta en Interruptor {id_interruptor.nombre}",
                        "",
                        settings.DEFAULT_FROM_EMAIL,
                        ["test@example.com"],
                        fail_silently=True,
                        html_message=html_body,
                    )
                else:
                    message = MIMEMultipart()
                    message["From"] = sender_email
                    message["To"] = receiver_email
                    message["Subject"] = f"🚨 Alerta en Interruptor {id_interruptor.nombre}"
                    message.attach(MIMEText(html_body, "html"))

                    server = None
                    try:
                        server = smtplib.SMTP(smtp_server, int(smtp_port))
                        server.starttls()
                        server.login(sender_email, password)
                        server.sendmail(sender_email, receiver_email, message.as_string())
                        print("✅ Correo de alerta enviado con éxito")
                    finally:
                        if server:
                            try:
                                server.quit()
                            except Exception:
                                pass

            except Exception as e:
                print(f"❌ Error al enviar el correo: {e}")

        return alerta

    @staticmethod
    def enviar_pronostico_interruptor(pronostico_data, interruptor_nombre, usuario_email, usuario_nombre=None):
        color_alerta_html = {
            "Azul": "#007bff",
            "Verde": "#28a745",
            "Amarillo": "#ffc107",
            "Naranja": "#fd7e14",
            "Rojo": "#dc3545"
        }

        # I_M se almacena normalizado en 0-1; se escala a % para clasificar.
        I_M = float(pronostico_data.get('I_M') or 0) * 100
        if 86 <= I_M <= 100:
            condicion, color_alerta = "Muy Bueno", "Azul"
        elif 71 <= I_M <= 85:
            condicion, color_alerta = "Bueno", "Verde"
        elif 51 <= I_M <= 70:
            condicion, color_alerta = "Regular", "Amarillo"
        elif 31 <= I_M <= 50:
            condicion, color_alerta = "Pobre", "Naranja"
        else:
            condicion, color_alerta = "Muy Pobre", "Rojo"

        color_texto = color_alerta_html.get(color_alerta, "#6c757d")
        fecha_envio = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        Pmant = pronostico_data.get('Pmant')
        pmant_str = f"{float(Pmant) * 100:.2f}%" if Pmant is not None else "N/A"

        html_body = f"""
        <html>
        <head>
            <style>
                body {{ background-color: #f0f0f5; font-family: 'Arial', sans-serif; padding: 0; margin: 0; }}
                .container {{ display: flex; justify-content: center; align-items: center; padding: 20px; background-color: #f0f0f5; }}
                .alert-box {{ background-color: white; border-radius: 12px; box-shadow: 0 0 10px rgba(0,0,0,0.1); padding: 30px; max-width: 600px; width: 100%; margin: auto; border-top: 6px solid {color_texto}; }}
                h1 {{ color: #333; font-size: 24px; text-align: center; margin-bottom: 20px; }}
                p {{ font-size: 16px; color: #333; line-height: 1.6; margin: 8px 0; }}
                .highlight {{ font-weight: bold; color: #000; }}
                .alert-color {{ color: {color_texto}; font-weight: bold; }}
                .section {{ margin: 15px 0; padding: 15px; background-color: #f8f9fa; border-radius: 8px; }}
                .section-title {{ font-weight: bold; color: #495057; margin-bottom: 10px; font-size: 14px; text-transform: uppercase; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="alert-box">
                    <h1>Pronostico de Interruptor</h1>
                    {f'<p>Estimado(a) <strong>{usuario_nombre}</strong>,</p>' if usuario_nombre else ''}
                    <p>A continuacion se presenta la informacion del pronostico solicitado:</p>
                    <hr style="margin: 15px 0;">
                    <div class="section">
                        <div class="section-title">Informacion General</div>
                        <p><span class="highlight">Interruptor:</span> {interruptor_nombre}</p>
                        <p><span class="highlight">ID Pronostico:</span> {pronostico_data.get('idpronostico', 'N/A')}</p>
                        <p><span class="highlight">Fecha de Creacion:</span> {pronostico_data.get('fecha_creacion', 'N/A')}</p>
                        <p><span class="highlight">Fecha Ultimo Mantenimiento:</span> {pronostico_data.get('fecha_mantenimiento', 'N/A')}</p>
                        <p><span class="highlight">Fecha Recomendada:</span> {pronostico_data.get('fecha_recomendada', 'N/A')}</p>
                    </div>
                    <div class="section">
                        <div class="section-title">Indices de Estado</div>
                        <p><span class="highlight">I_DM:</span> {pronostico_data.get('I_DM', 'N/A')}</p>
                        <p><span class="highlight">I_EE:</span> {pronostico_data.get('I_EE', 'N/A')}</p>
                        <p><span class="highlight">I_M actual:</span> <span class="alert-color">{pronostico_data.get('I_M', 'N/A')}</span></p>
                        <p><span class="highlight">I_M anterior:</span> {pronostico_data.get('I_M_prev', 'N/A')}</p>
                        <p><span class="highlight">Delta IM:</span> {pronostico_data.get('delta_IM', 'N/A')}</p>
                        <p><span class="highlight">Pmant:</span> {pmant_str}</p>
                    </div>
                    <div class="section">
                        <div class="section-title">Condicion</div>
                        <p><span class="highlight">Estado:</span> <span class="alert-color">{condicion}</span></p>
                        <p><span class="highlight">Nivel de Alerta:</span> <span class="alert-color">{color_alerta}</span></p>
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
        subject = f"Pronostico Interruptor: {interruptor_nombre}"

        if os.getenv('ENABLE_MAILHOG', 'False') == 'True':
            try:
                send_mail(
                    subject, "", settings.DEFAULT_FROM_EMAIL,
                    [usuario_email], fail_silently=False, html_message=html_body,
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
                server = smtplib.SMTP(smtp_server, int(smtp_port))
                server.starttls()
                server.login(sender_email, password)
                server.sendmail(sender_email, usuario_email, message.as_string())
                return {"success": True, "message": "Correo enviado exitosamente"}
            except Exception as e:
                return {"success": False, "message": f"Error al enviar el correo: {str(e)}"}
            finally:
                if server:
                    server.quit()
