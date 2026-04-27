import os
import smtplib
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import joblib
import numpy as np
from datetime import timedelta, datetime
from django.utils import timezone
from django.conf import settings

from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import (
    MedicionesTransformadores,
    Analisisaceitefisicoquimico,
    Analisisgasesdisueltos,
    Alertas,
    Transformadores,
    Interruptores,
    MedicionesInterruptores,
    AlertasInterruptores,
    Pronosticos,
    PronosticosTransformadores
)

User = get_user_model()


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        try:
            user = User.objects.filter(correo=data['username']).first()

            if user and user.check_password(data['password']):
                refresh = RefreshToken.for_user(user)
                return {
                    'refresh': str(refresh),
                    'token': str(refresh.access_token),
                    'rol': user.rol,
                    'Nombres': user.nombre,
                    'idUsuario': user.idusuario
                }
            else:
                raise serializers.ValidationError('Invalid username or password')
        except:
            raise serializers.ValidationError('Invalid username or password')


class UsuarioSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['idusuario', 'correo', 'rol', 'password', 'nombre', 'estado']
        extra_kwargs = {'password': {'write_only': True}}

    def create(self, validated_data):

        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        print(instance.password)
        for attr, value in validated_data.items():
            if attr == 'password':
                instance.set_password(value)
            else:
                setattr(instance, attr, value)
        instance.save()
        print(instance.password)
        return instance


class AnalisisAceiteFisicoQuimicoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analisisaceitefisicoquimico
        fields = '__all__'
        extra_kwargs = {
            'mediciones_transformadores_idmediciones_transformadores': {'required': False}
        }


class AnalisisGasesDisueltosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Analisisgasesdisueltos
        fields = '__all__'

        extra_kwargs = {
            'mediciones_transformadores_idmediciones_transformadores': {'required': False}
        }


class MedicionesTransformadoresSerializer(serializers.ModelSerializer):
    analisis_aceite_fisico_quimico = AnalisisAceiteFisicoQuimicoSerializer(write_only=True)
    analisis_gases_disueltos = AnalisisGasesDisueltosSerializer(write_only=True)

    transformadores = serializers.PrimaryKeyRelatedField(
        queryset=Transformadores.objects.all(), required=False
    )

    class Meta:
        model = MedicionesTransformadores
        fields = '__all__'

    def validate(self, data):
        # ========== VALIDACIONES ANTERIORES (BACKUP) ==========
        # if data['relacion_transformacion'] < 0 or data['relacion_transformacion'] > 1:
        #     raise serializers.ValidationError({"relacion_transformacion": "Debe estar entre 0 y 1."})
        #
        # if data['resistencia_devanados'] < 0 or data['resistencia_devanados'] > 1:
        #     raise serializers.ValidationError({"resistencia_devanados": "Debe estar entre 0 y 1."})
        #
        # if data['factor_potencia'] < 0 or data['factor_potencia'] > 1:
        #     raise serializers.ValidationError({"factor_potencia": "Debe estar entre 0 y 1."})
        # ========== FIN VALIDACIONES ANTERIORES ==========

        # Validación corregida según lógica de cálculo (líneas 324-373)
        # Las validaciones fueron ajustadas porque la lógica contempla valores mayores a 1
        if data['relacion_transformacion'] < 0:
            raise serializers.ValidationError({"relacion_transformacion": "Debe ser mayor o igual a 0."})

        if data['resistencia_devanados'] < 0:
            raise serializers.ValidationError({"resistencia_devanados": "Debe ser mayor o igual a 0."})

        if data['corriente_excitacion'] < 0 or data['corriente_excitacion'] > 7:
            raise serializers.ValidationError({"corriente_excitacion": "Debe estar entre 0 y 7."})

        if data['factor_potencia'] < 0:
            raise serializers.ValidationError({"factor_potencia": "Debe ser mayor o igual a 0."})

        if data['inhibidor_oxidacion'] < 0 or data['inhibidor_oxidacion'] > 1:
            raise serializers.ValidationError({"inhibidor_oxidacion": "Debe estar entre 0 y 1."})

        return data

    def perform_calculations(self, validated_data, instance=None):
        # Extraer datos relacionados
        analisis_aceite_data = validated_data.pop('analisis_aceite_fisico_quimico')
        analisis_gases_data = validated_data.pop('analisis_gases_disueltos')

        analisis_aceite = Analisisaceitefisicoquimico(**analisis_aceite_data)
        analisis_gases = Analisisgasesdisueltos(**analisis_gases_data)
        data_mediciones = MedicionesTransformadores(**validated_data)

        gases_peso_array = []
        gases_puntaje_array = []

        gases_peso_array.append(2)
        if (analisis_gases.hidrogeno <= 100):
            gases_puntaje_array.append(1)
        if (analisis_gases.hidrogeno >= 101 and analisis_gases.hidrogeno <= 200):
            gases_puntaje_array.append(2)
        if (analisis_gases.hidrogeno >= 201 and analisis_gases.hidrogeno <= 300):
            gases_puntaje_array.append(3)
        if (analisis_gases.hidrogeno >= 301 and analisis_gases.hidrogeno <= 500):
            gases_puntaje_array.append(4)
        if (analisis_gases.hidrogeno >= 501 and analisis_gases.hidrogeno <= 700):
            gases_puntaje_array.append(5)
        if (analisis_gases.hidrogeno > 700):
            gases_puntaje_array.append(6)

        gases_peso_array.append(3)
        if (analisis_gases.metano <= 75):
            gases_puntaje_array.append(1)
        if (analisis_gases.metano >= 76 and analisis_gases.metano <= 125):
            gases_puntaje_array.append(2)
        if (analisis_gases.metano >= 126 and analisis_gases.metano <= 200):
            gases_puntaje_array.append(3)
        if (analisis_gases.metano >= 201 and analisis_gases.metano <= 400):
            gases_puntaje_array.append(4)
        if (analisis_gases.metano >= 401 and analisis_gases.metano <= 600):
            gases_puntaje_array.append(5)
        if (analisis_gases.metano > 600):
            gases_puntaje_array.append(6)

        gases_peso_array.append(1)
        if (analisis_gases.etano <= 65):
            gases_puntaje_array.append(1)
        if (analisis_gases.etano >= 66 and analisis_gases.etano <= 80):
            gases_puntaje_array.append(2)
        if (analisis_gases.etano >= 81 and analisis_gases.etano <= 100):
            gases_puntaje_array.append(3)
        if (analisis_gases.etano >= 101 and analisis_gases.etano <= 120):
            gases_puntaje_array.append(4)
        if (analisis_gases.etano >= 121 and analisis_gases.etano <= 150):
            gases_puntaje_array.append(5)
        if (analisis_gases.etano > 150):
            gases_puntaje_array.append(6)

        gases_peso_array.append(3)
        if (analisis_gases.etileno <= 50):
            gases_puntaje_array.append(1)
        if (analisis_gases.etileno >= 51 and analisis_gases.etileno <= 80):
            gases_puntaje_array.append(2)
        if (analisis_gases.etileno >= 81 and analisis_gases.etileno <= 100):
            gases_puntaje_array.append(3)
        if (analisis_gases.etileno >= 101 and analisis_gases.etileno <= 150):
            gases_puntaje_array.append(4)
        if (analisis_gases.etileno >= 151 and analisis_gases.etileno <= 200):
            gases_puntaje_array.append(5)
        if (analisis_gases.etileno > 200):
            gases_puntaje_array.append(6)

        gases_peso_array.append(5)
        if (analisis_gases.acetileno <= 3):
            gases_puntaje_array.append(1)
        if (analisis_gases.acetileno >= 4 and analisis_gases.acetileno <= 7):
            gases_puntaje_array.append(2)
        if (analisis_gases.acetileno >= 8 and analisis_gases.acetileno <= 35):
            gases_puntaje_array.append(3)
        if (analisis_gases.acetileno >= 36 and analisis_gases.acetileno <= 50):
            gases_puntaje_array.append(4)
        if (analisis_gases.acetileno >= 51 and analisis_gases.acetileno <= 80):
            gases_puntaje_array.append(5)
        if (analisis_gases.acetileno > 80):
            gases_puntaje_array.append(6)

        gases_peso_array.append(1)
        if (analisis_gases.dioxido_carbono <= 350):
            gases_puntaje_array.append(1)
        if (analisis_gases.dioxido_carbono >= 351 and analisis_gases.dioxido_carbono <= 700):
            gases_puntaje_array.append(2)
        if (analisis_gases.dioxido_carbono >= 701 and analisis_gases.dioxido_carbono <= 900):
            gases_puntaje_array.append(3)
        if (analisis_gases.dioxido_carbono >= 901 and analisis_gases.dioxido_carbono <= 1100):
            gases_puntaje_array.append(4)
        if (analisis_gases.dioxido_carbono >= 1101 and analisis_gases.dioxido_carbono <= 1400):
            gases_puntaje_array.append(5)
        if (analisis_gases.dioxido_carbono > 1400):
            gases_puntaje_array.append(6)

        gases_peso_array.append(1)
        if (analisis_gases.monoxido_carbono <= 2500):
            gases_puntaje_array.append(1)
        elif (analisis_gases.monoxido_carbono <= 3000):
            gases_puntaje_array.append(2)
        elif (analisis_gases.monoxido_carbono <= 4000):
            gases_puntaje_array.append(3)
        elif (analisis_gases.monoxido_carbono <= 5000):
            gases_puntaje_array.append(4)
        elif (analisis_gases.monoxido_carbono <= 6000):
            gases_puntaje_array.append(5)
        elif (analisis_gases.monoxido_carbono > 6000):
            gases_puntaje_array.append(6)

        max_puntaje = max(gases_puntaje_array)
        numerador = 0
        denominador = 0

        for index, valor in enumerate(gases_peso_array):
            numerador += (valor * gases_puntaje_array[index])
            denominador += (max_puntaje * valor)

        gases_disueltos = round((numerador / denominador) * 100, 4)

        aceite_peso_array = []
        aceite_puntaje_array = []

        aceite_peso_array.append(3)
        if (analisis_aceite.rigidez_dieletrica >= 45):
            aceite_puntaje_array.append(1)
        if (analisis_aceite.rigidez_dieletrica < 45 and analisis_aceite.rigidez_dieletrica >= 35):
            aceite_puntaje_array.append(2)
        if (analisis_aceite.rigidez_dieletrica < 35 and analisis_aceite.rigidez_dieletrica >= 30):
            aceite_puntaje_array.append(3)
        if (analisis_aceite.rigidez_dieletrica < 30):
            aceite_puntaje_array.append(4)

        aceite_peso_array.append(2)
        if (analisis_aceite.tension_interfacial >= 25):
            aceite_puntaje_array.append(1)
        if (analisis_aceite.tension_interfacial < 25 and analisis_aceite.tension_interfacial >= 20):
            aceite_puntaje_array.append(2)
        if (analisis_aceite.tension_interfacial < 20 and analisis_aceite.tension_interfacial >= 15):
            aceite_puntaje_array.append(3)
        if (analisis_aceite.tension_interfacial < 15):
            aceite_puntaje_array.append(4)

        aceite_peso_array.append(1)
        if (analisis_aceite.numero_acidez <= 0.05):
            aceite_puntaje_array.append(1)
        if (analisis_aceite.numero_acidez > 0.05 and analisis_aceite.numero_acidez <= 0.1):
            aceite_puntaje_array.append(2)
        if (analisis_aceite.numero_acidez > 0.1 and analisis_aceite.numero_acidez <= 0.2):
            aceite_puntaje_array.append(3)
        if (analisis_aceite.numero_acidez > 0.2):
            aceite_puntaje_array.append(4)

        aceite_peso_array.append(4)
        if (analisis_aceite.contenido_humedad <= 15):
            aceite_puntaje_array.append(1)
        if (analisis_aceite.contenido_humedad > 15 and analisis_aceite.contenido_humedad <= 20):
            aceite_puntaje_array.append(2)
        if (analisis_aceite.contenido_humedad > 20 and analisis_aceite.contenido_humedad <= 25):
            aceite_puntaje_array.append(3)
        if (analisis_aceite.contenido_humedad > 25):
            aceite_puntaje_array.append(4)

        aceite_peso_array.append(2)
        if (analisis_aceite.color <= 1.5):
            aceite_puntaje_array.append(1)
        if (analisis_aceite.color > 1.5 and analisis_aceite.color <= 2.0):
            aceite_puntaje_array.append(2)
        if (analisis_aceite.color > 2.0 and analisis_aceite.color <= 2.5):
            aceite_puntaje_array.append(3)
        if (analisis_aceite.color > 2.5):
            aceite_puntaje_array.append(4)

        aceite_peso_array.append(2)
        factor = analisis_aceite.factor_potencia_liquido * Decimal(0.25)
        if (factor <= 0.1):
            aceite_puntaje_array.append(1)
        if (factor > 0.1 and factor <= 0.5):
            aceite_puntaje_array.append(2)
        if (factor > 0.5 and factor <= 1.0):
            aceite_puntaje_array.append(3)
        if (factor > 1.0):
            aceite_puntaje_array.append(4)

        numerador = 0
        denominador = 0

        for index, valor in enumerate(aceite_peso_array):
            numerador += (valor * aceite_puntaje_array[index])
            denominador += valor

        calidad_aceite = round((numerador / denominador) * 100, 4)

        hi_funcional_puntaje_array = []

        if (data_mediciones.relacion_transformacion <= 0.1):
            hi_funcional_puntaje_array.append(4)
        if (data_mediciones.relacion_transformacion > 0.1 and data_mediciones.relacion_transformacion <= 0.5):
            hi_funcional_puntaje_array.append(3)
        if (data_mediciones.relacion_transformacion > 0.5 and data_mediciones.relacion_transformacion <= 1.0):
            hi_funcional_puntaje_array.append(2)
        if (data_mediciones.relacion_transformacion > 1.0 and data_mediciones.relacion_transformacion <= 2.0):
            hi_funcional_puntaje_array.append(1)
        if (data_mediciones.relacion_transformacion > 2.0):
            hi_funcional_puntaje_array.append(0)

        if (data_mediciones.resistencia_devanados <= 1):
            hi_funcional_puntaje_array.append(4)
        if (data_mediciones.resistencia_devanados > 1 and data_mediciones.resistencia_devanados <= 2):
            hi_funcional_puntaje_array.append(3)
        if (data_mediciones.resistencia_devanados > 2 and data_mediciones.resistencia_devanados <= 3):
            hi_funcional_puntaje_array.append(2)
        if (data_mediciones.resistencia_devanados > 3 and data_mediciones.resistencia_devanados <= 5):
            hi_funcional_puntaje_array.append(1)
        if (data_mediciones.resistencia_devanados > 5):
            hi_funcional_puntaje_array.append(0)

        if (data_mediciones.corriente_excitacion == 5 or data_mediciones.corriente_excitacion == 2):
            hi_funcional_puntaje_array.append(4)
        else:
            hi_funcional_puntaje_array.append(0)

        if (gases_disueltos <= 20):
            hi_funcional_puntaje_array.append(4)
        if (gases_disueltos > 20 and gases_disueltos <= 30):
            hi_funcional_puntaje_array.append(3)
        if (gases_disueltos > 30 and gases_disueltos <= 40):
            hi_funcional_puntaje_array.append(2)
        if (gases_disueltos > 40 and gases_disueltos <= 50):
            hi_funcional_puntaje_array.append(1)
        if (gases_disueltos > 50):
            hi_funcional_puntaje_array.append(0)

        hi_dielectrico_puntaje_array = []

        if (data_mediciones.factor_potencia <= 0.5):
            hi_dielectrico_puntaje_array.append(4)
        if (data_mediciones.factor_potencia > 0.5 and data_mediciones.factor_potencia <= 0.7):
            hi_dielectrico_puntaje_array.append(3)
        if (data_mediciones.factor_potencia > 0.7 and data_mediciones.factor_potencia <= 1):
            hi_dielectrico_puntaje_array.append(2)
        if (data_mediciones.factor_potencia > 1 and data_mediciones.factor_potencia <= 2):
            hi_dielectrico_puntaje_array.append(1)
        if (data_mediciones.factor_potencia > 2):
            hi_dielectrico_puntaje_array.append(0)

        if (calidad_aceite <= 1.2):
            hi_dielectrico_puntaje_array.append(4)
        if (calidad_aceite > 1.2 and calidad_aceite <= 1.5):
            hi_dielectrico_puntaje_array.append(3)
        if (calidad_aceite > 1.5 and calidad_aceite <= 2):
            hi_dielectrico_puntaje_array.append(2)
        if (calidad_aceite > 2 and calidad_aceite <= 3):
            hi_dielectrico_puntaje_array.append(1)
        if (calidad_aceite > 3):
            hi_dielectrico_puntaje_array.append(0)

        if (data_mediciones.inhibidor_oxidacion > 0.25):
            hi_dielectrico_puntaje_array.append(4)
        if (data_mediciones.inhibidor_oxidacion <= 0.25 and data_mediciones.inhibidor_oxidacion > 0.2):
            hi_dielectrico_puntaje_array.append(3)
        if (data_mediciones.inhibidor_oxidacion <= 0.2 and data_mediciones.inhibidor_oxidacion > 0.15):
            hi_dielectrico_puntaje_array.append(2)
        if (data_mediciones.inhibidor_oxidacion <= 0.15 and data_mediciones.inhibidor_oxidacion > 0.1):
            hi_dielectrico_puntaje_array.append(1)
        if (data_mediciones.inhibidor_oxidacion <= 0.1):
            hi_dielectrico_puntaje_array.append(0)

        if (data_mediciones.compuestos_furanicos > 700):
            hi_dielectrico_puntaje_array.append(4)
        if (data_mediciones.compuestos_furanicos <= 700 and data_mediciones.compuestos_furanicos > 560):
            hi_dielectrico_puntaje_array.append(3)
        if (data_mediciones.compuestos_furanicos <= 560 and data_mediciones.compuestos_furanicos > 425):
            hi_dielectrico_puntaje_array.append(2)
        if (data_mediciones.compuestos_furanicos <= 425 and data_mediciones.compuestos_furanicos > 250):
            hi_dielectrico_puntaje_array.append(1)
        if (data_mediciones.compuestos_furanicos <= 250):
            hi_dielectrico_puntaje_array.append(0)

        history_data = []

        if (instance != None):
            history_data = MedicionesTransformadores.objects.exclude(
                idmediciones_transformadores=instance.idmediciones_transformadores)
        else:
            history_data = MedicionesTransformadores.objects.filter()

        numerador_dielectrico = ((hi_dielectrico_puntaje_array[0] * 10) +
                                 (hi_dielectrico_puntaje_array[1] * 6) +
                                 (hi_dielectrico_puntaje_array[2] * 3) +
                                 (hi_dielectrico_puntaje_array[3] * 8))
        denominador_dielectrico = 4 * (10 + 6 + 3 + 8)

        numerador_funcional = ((hi_funcional_puntaje_array[0] * 8) +
                               (hi_funcional_puntaje_array[1] * 6) +
                               (hi_funcional_puntaje_array[2] * 5) +
                               (hi_funcional_puntaje_array[3] * 10))

        denominador_funcional = 4 * (8 + 6 + 5 + 10)

        for data in history_data:
            numerador_funcional += ((data.hif_relacion_transformacion * 8) +
                                    (data.hif_resistencia_devanados * 6) +
                                    (data.hif_corriente_excitacion * 5) +
                                    (data.hif_gases_disueltos * 10))
            denominador_funcional += 4 * (8 + 6 + 5 + 10)

            numerador_dielectrico += ((data.hi_factor_potencia * 10) +
                                      (data.hi_inhibidor_oxidacion * 6) +
                                      (data.hi_compuestos_furanicos * 3) +
                                      (data.hi_calidad_aceite_humedad * 8))
            denominador_dielectrico += 4 * (10 + 6 + 3 + 8)

        hi_funcional = Decimal((numerador_funcional / denominador_funcional) * 100)
        hi_dielectrico = Decimal((numerador_dielectrico / denominador_dielectrico) * 100)

        hi_ponderado = Decimal(0.5) * hi_funcional + Decimal(0.5) * hi_dielectrico
        return {
            "calidad_aceite_humedad": calidad_aceite,
            "gases_disueltos": gases_disueltos,
            "hif_relacion_transformacion": hi_funcional_puntaje_array[0],
            "hif_resistencia_devanados": hi_funcional_puntaje_array[1],
            "hif_corriente_excitacion": hi_funcional_puntaje_array[2],
            "hif_gases_disueltos": hi_funcional_puntaje_array[3],
            "hi_factor_potencia": hi_dielectrico_puntaje_array[0],
            "hi_inhibidor_oxidacion": hi_dielectrico_puntaje_array[1],
            "hi_compuestos_furanicos": hi_dielectrico_puntaje_array[2],
            "hi_calidad_aceite_humedad": hi_dielectrico_puntaje_array[3],
            "hi_dielectrico": hi_dielectrico,
            "hi_funcional": hi_funcional,
            "hi_ponderado": Decimal(hi_ponderado),
            "analisis_aceite": analisis_aceite,
            "analisis_gases": analisis_gases,
        }

    def generar_alerta(self, hi_ponderado, id_transformador):

        send_message = False

        if hi_ponderado <= 100 and hi_ponderado > 85:
            alerta = {
                "mensaje_condicion": "Muy Bueno",
                "vida_util_remanente": "Más de 15 Años",
                "recomendacion": "Continuo mantenimiento normal",
                "color_alerta": "Azul",
            }

        if hi_ponderado <= 85 and hi_ponderado > 70:
            alerta = {
                "mensaje_condicion": "Bueno",
                "vida_util_remanente": "Más de 10 Años",
                "recomendacion": "Continuo mantenimiento normal",
                "color_alerta": "Verde",
            }

        if hi_ponderado <= 70 and hi_ponderado > 50:
            send_message = True
            alerta = {
                "mensaje_condicion": "Regular",
                "vida_util_remanente": "Hasta de 10 Años",
                "recomendacion": "Generar alerta amarilla para incremento de pruebas de rutina",
                "color_alerta": "Amarillo",
            }

        if hi_ponderado <= 50 and hi_ponderado > 30:
            send_message = True
            alerta = {
                "mensaje_condicion": "Pobre",
                "vida_util_remanente": "Menos de 10 Años",
                "recomendacion": "Generar alerta naranja para aumentar las pruebas de rutina y programar posible cambio",
                "color_alerta": "Naranja",
            }

        if hi_ponderado <= 30 and hi_ponderado > 0:
            send_message = True
            alerta = {
                "mensaje_condicion": "Muy Pobre",
                "vida_util_remanente": "Fin de vida útil",
                "recomendacion": "Generar alerta roja para programar cambiar lo antes posible",
                "color_alerta": "Rojo",
            }

        if send_message:
            smtp_server = os.getenv('SMTP_SERVER')
            smtp_port = os.getenv('SMTP_PORT')
            sender_email = os.getenv('SENDER_EMAIL')
            password = os.getenv('PASSWORD_EMAIL')
            receiver_email = os.getenv('FROM_EMAIL')

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = receiver_email
            message["Subject"] = "Alerta " + alerta["color_alerta"]

            print(id_transformador)

            html_body = """
                <html>
                <body>
                    <h1>¡Hola!</h1>
                    <p> Transformador: """ + str(id_transformador.idtransformadores) + """</p>
                    <p> Condición: """ + alerta['mensaje_condicion'] + """</p>
                    <p> Vida util remanente:""" + alerta['vida_util_remanente'] + """</p>
                    <p> Recomendación: """ + alerta['recomendacion'] + """</p>
                    <p> Tipo alerta: """ + alerta['color_alerta'] + """</p>
                </body>
                </html>
            """

            message.attach(MIMEText(html_body, "html"))

            # Conexión al servidor SMTP con TLS
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Inicia la conexión segura

            # Autenticación
            server.login(sender_email, password)

            # Envía el correo
            server.sendmail(sender_email, receiver_email, message.as_string())
            print("Correo enviado con éxito")

        return alerta

    def create(self, validated_data):

        data = self.perform_calculations(validated_data)

        # Crear medición
        medicion = MedicionesTransformadores.objects.create(
            calidad_aceite_humedad=data["calidad_aceite_humedad"],
            gases_disueltos=data["gases_disueltos"],
            hif_relacion_transformacion=data["hif_relacion_transformacion"],
            hif_resistencia_devanados=data["hif_resistencia_devanados"],
            hif_corriente_excitacion=data["hif_corriente_excitacion"],
            hif_gases_disueltos=data["hif_gases_disueltos"],
            hi_factor_potencia=data["hi_factor_potencia"],
            hi_inhibidor_oxidacion=data["hi_inhibidor_oxidacion"],
            hi_compuestos_furanicos=data["hi_compuestos_furanicos"],
            hi_calidad_aceite_humedad=data["hi_calidad_aceite_humedad"],
            hi_dielectrico=data["hi_dielectrico"],
            hi_funcional=data["hi_funcional"],
            hi_ponderado=data["hi_ponderado"],
            **validated_data
        )

        data['analisis_aceite'].mediciones_transformadores_idmediciones_transformadores = medicion
        data['analisis_aceite'].save()
        data['analisis_gases'].mediciones_transformadores_idmediciones_transformadores = medicion
        data['analisis_gases'].save()

        data_mediciones = MedicionesTransformadores(**validated_data)

        alerta = self.generar_alerta(data["hi_ponderado"], data_mediciones.transformadores)
        Alertas.objects.create(
            mediciones_transformadores=medicion,
            **alerta
        )

        return medicion

    def update(self, instance, validated_data):
        # Llama a la lógica común
        data = self.perform_calculations(validated_data, instance)

        update_data = {
            "calidad_aceite_humedad": data["calidad_aceite_humedad"],
            "gases_disueltos": data["gases_disueltos"],
            "hif_relacion_transformacion": data["hif_relacion_transformacion"],
            "hif_resistencia_devanados": data["hif_resistencia_devanados"],
            "hif_corriente_excitacion": data["hif_corriente_excitacion"],
            "hif_gases_disueltos": data["hif_gases_disueltos"],
            "hi_factor_potencia": data["hi_factor_potencia"],
            "hi_inhibidor_oxidacion": data["hi_inhibidor_oxidacion"],
            "hi_compuestos_furanicos": data["hi_compuestos_furanicos"],
            "hi_calidad_aceite_humedad": data["hi_calidad_aceite_humedad"],
            "hi_dielectrico": data["hi_dielectrico"],
            "hi_funcional": data["hi_funcional"],
            "hi_ponderado": data["hi_ponderado"],
            **validated_data
        }
        # Actualiza la instancia con los datos procesados
        return super().update(instance, update_data)


class AlertasSerializer(serializers.ModelSerializer):
    class Meta:
        model = Alertas
        fields = '__all__'


class AlertasInterruptoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertasInterruptores
        fields = '__all__'


class TransformadoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transformadores
        exclude = ['deleted']


class InterruptoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Interruptores
        exclude = ['deleted']


class MedicionesInterruptoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicionesInterruptores
        fields = '__all__'


class PronosticosSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pronosticos
        fields = '__all__'
        read_only_fields = ['I_DM', 'I_EE', 'I_M', 'I_M_prev', 'delta_IM', 'Pmant', 'fecha_creacion']


class PronosticosTransformadoresSerializer(serializers.ModelSerializer):
    """
    Serializer para pronósticos de transformadores.
    Calcula HI, RM y fechas de mantenimiento usando el servicio PronosticoTransformador.
    """
    class Meta:
        model = PronosticosTransformadores
        fields = '__all__'
        read_only_fields = [
            'hif_relacion_transformacion', 'hif_resistencia_devanados',
            'hif_corriente_excitacion', 'dgaf_porcentaje', 'hif_gases_disueltos',
            'hif_factor_potencia', 'oqf_porcentaje', 'hif_calidad_aceite',
            'hif_inhibidor_oxidacion', 'hif_grado_polimerizacion',
            'hi_funcional', 'hi_dielectrico', 'hi_total',
            'faa_p95', 'estres_termico', 'rm_actual', 'tendencia_hi',
            'fecha_cruce_rm', 'fecha_programada', 'fecha_optima_sugerida',
            'criterio_fecha', 'condicion_hi', 'vida_util_remanente',
            'recomendacion', 'color_alerta', 'fecha_creacion'
        ]
        extra_kwargs = {
            'relacion_transformacion': {'required': False},
            'resistencia_devanados': {'required': False},
            'corriente_excitacion': {'required': False},
            'hidrogeno': {'required': False},
            'metano': {'required': False},
            'etano': {'required': False},
            'etileno': {'required': False},
            'acetileno': {'required': False},
            'dioxido_carbono': {'required': False},
            'monoxido_carbono': {'required': False},
            'factor_potencia': {'required': False},
            'rigidez_dielectrica': {'required': False},
            'tension_interfacial': {'required': False},
            'numero_acidez': {'required': False},
            'contenido_humedad': {'required': False},
            'color': {'required': False},
            'factor_potencia_liquido': {'required': False},
            'inhibidor_oxidacion': {'required': False},
            'grado_polimerizacion': {'required': False},
        }

    def validate(self, data):
        if not data.get('transformador'):
            raise serializers.ValidationError({"transformador": "Debe proporcionar un transformador."})
        if not data.get('fecha_ultimo_mantenimiento'):
            raise serializers.ValidationError({"fecha_ultimo_mantenimiento": "Debe proporcionar la fecha del último mantenimiento."})
        return data

    def create(self, validated_data):
        from services.PronosticoTransformador import PronosticoTransformador

        transformador = validated_data.get('transformador')

        # Buscar la última medición del transformador
        ultima_medicion = (
            MedicionesTransformadores.objects
            .filter(transformadores=transformador)
            .order_by('-fecha_hora')
            .first()
        )
        if not ultima_medicion:
            raise serializers.ValidationError(
                {"transformador": "El transformador no tiene mediciones registradas."}
            )

        # Buscar gases disueltos y aceite físico-químico de esa medición
        try:
            gases = Analisisgasesdisueltos.objects.get(
                mediciones_transformadores_idmediciones_transformadores=ultima_medicion
            )
        except Analisisgasesdisueltos.DoesNotExist:
            raise serializers.ValidationError(
                {"transformador": "La última medición no tiene análisis de gases disueltos."}
            )

        try:
            aceite = Analisisaceitefisicoquimico.objects.get(
                mediciones_transformadores_idmediciones_transformadores=ultima_medicion
            )
        except Analisisaceitefisicoquimico.DoesNotExist:
            raise serializers.ValidationError(
                {"transformador": "La última medición no tiene análisis de aceite físico-químico."}
            )

        # Construir datos de entrada desde las 3 tablas
        datos_entrada = {
            'relacion_transformacion': float(ultima_medicion.relacion_transformacion),
            'resistencia_devanados': float(ultima_medicion.resistencia_devanados),
            'corriente_excitacion': int(ultima_medicion.corriente_excitacion),
            'hidrogeno': float(gases.hidrogeno),
            'metano': float(gases.metano),
            'etano': float(gases.etano),
            'etileno': float(gases.etileno),
            'acetileno': float(gases.acetileno),
            'dioxido_carbono': float(gases.dioxido_carbono),
            'monoxido_carbono': float(gases.monoxido_carbono),
            'factor_potencia': float(ultima_medicion.factor_potencia),
            'rigidez_dielectrica': float(aceite.rigidez_dieletrica),
            'tension_interfacial': float(aceite.tension_interfacial),
            'numero_acidez': float(aceite.numero_acidez),
            'contenido_humedad': float(aceite.contenido_humedad),
            'color': float(aceite.color),
            'factor_potencia_liquido': float(aceite.factor_potencia_liquido),
            'inhibidor_oxidacion': float(ultima_medicion.inhibidor_oxidacion),
            'grado_polimerizacion': float(ultima_medicion.compuestos_furanicos),
        }

        # Persistir los valores de entrada en el pronóstico
        validated_data['relacion_transformacion'] = Decimal(str(datos_entrada['relacion_transformacion']))
        validated_data['resistencia_devanados'] = Decimal(str(datos_entrada['resistencia_devanados']))
        validated_data['corriente_excitacion'] = datos_entrada['corriente_excitacion']
        validated_data['hidrogeno'] = Decimal(str(datos_entrada['hidrogeno']))
        validated_data['metano'] = Decimal(str(datos_entrada['metano']))
        validated_data['etano'] = Decimal(str(datos_entrada['etano']))
        validated_data['etileno'] = Decimal(str(datos_entrada['etileno']))
        validated_data['acetileno'] = Decimal(str(datos_entrada['acetileno']))
        validated_data['dioxido_carbono'] = Decimal(str(datos_entrada['dioxido_carbono']))
        validated_data['monoxido_carbono'] = Decimal(str(datos_entrada['monoxido_carbono']))
        validated_data['factor_potencia'] = Decimal(str(datos_entrada['factor_potencia']))
        validated_data['rigidez_dielectrica'] = Decimal(str(datos_entrada['rigidez_dielectrica']))
        validated_data['tension_interfacial'] = Decimal(str(datos_entrada['tension_interfacial']))
        validated_data['numero_acidez'] = Decimal(str(datos_entrada['numero_acidez']))
        validated_data['contenido_humedad'] = Decimal(str(datos_entrada['contenido_humedad']))
        validated_data['color'] = Decimal(str(datos_entrada['color']))
        validated_data['factor_potencia_liquido'] = Decimal(str(datos_entrada['factor_potencia_liquido']))
        validated_data['inhibidor_oxidacion'] = Decimal(str(datos_entrada['inhibidor_oxidacion']))
        validated_data['grado_polimerizacion'] = Decimal(str(datos_entrada['grado_polimerizacion']))

        fecha_ultimo_mant = validated_data.get('fecha_ultimo_mantenimiento')

        # Ejecutar cálculo de pronóstico
        pronostico_calc = PronosticoTransformador(datos_entrada, fecha_ultimo_mant)
        resultado = pronostico_calc.calcular_pronostico()

        # Agregar campos calculados a los datos validados
        validated_data['hif_relacion_transformacion'] = resultado.hif_relacion_transformacion
        validated_data['hif_resistencia_devanados'] = resultado.hif_resistencia_devanados
        validated_data['hif_corriente_excitacion'] = resultado.hif_corriente_excitacion
        validated_data['dgaf_porcentaje'] = Decimal(str(resultado.dgaf_porcentaje))
        validated_data['hif_gases_disueltos'] = resultado.hif_gases_disueltos

        validated_data['hif_factor_potencia'] = resultado.hif_factor_potencia
        validated_data['oqf_porcentaje'] = Decimal(str(resultado.oqf_porcentaje))
        validated_data['hif_calidad_aceite'] = resultado.hif_calidad_aceite
        validated_data['hif_inhibidor_oxidacion'] = resultado.hif_inhibidor_oxidacion
        validated_data['hif_grado_polimerizacion'] = resultado.hif_grado_polimerizacion

        validated_data['hi_funcional'] = Decimal(str(resultado.hi_funcional))
        validated_data['hi_dielectrico'] = Decimal(str(resultado.hi_dielectrico))
        validated_data['hi_total'] = Decimal(str(resultado.hi_total))

        validated_data['faa_p95'] = Decimal(str(resultado.faa_p95))
        validated_data['estres_termico'] = Decimal(str(resultado.estres_termico))

        validated_data['rm_actual'] = Decimal(str(resultado.rm_actual))
        validated_data['tendencia_hi'] = Decimal(str(resultado.tendencia_hi))

        validated_data['fecha_cruce_rm'] = resultado.fecha_cruce_rm
        validated_data['fecha_programada'] = resultado.fecha_programada
        validated_data['fecha_optima_sugerida'] = resultado.fecha_optima_sugerida
        validated_data['criterio_fecha'] = resultado.criterio_fecha

        validated_data['condicion_hi'] = resultado.condicion_hi
        validated_data['vida_util_remanente'] = resultado.vida_util_remanente
        validated_data['recomendacion'] = resultado.recomendacion
        validated_data['color_alerta'] = resultado.color_alerta

        # Crear el pronóstico
        return super().create(validated_data)
