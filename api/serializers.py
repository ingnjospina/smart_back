import os
import smtplib
from decimal import Decimal
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

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
    MedicionesInterruptores
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
        if data['relacion_transformacion'] < 0 or data['relacion_transformacion'] > 1:
            raise serializers.ValidationError({"relacion_transformacion": "Debe estar entre 0 y 1."})

        if data['resistencia_devanados'] < 0 or data['resistencia_devanados'] > 1:
            raise serializers.ValidationError({"resistencia_devanados": "Debe estar entre 0 y 1."})

        if data['corriente_excitacion'] < 0 or data['corriente_excitacion'] > 7:
            raise serializers.ValidationError({"corriente_excitacion": "Debe estar entre 0 y 7."})

        if data['factor_potencia'] < 0 or data['factor_potencia'] > 1:
            raise serializers.ValidationError({"factor_potencia": "Debe estar entre 0 y 1."})

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


class TransformadoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transformadores
        exclude = ['deleted']


class InterruptoresSerializer(serializers.ModelSerializer):
    idInterruptores = serializers.IntegerField(required=False)

    class Meta:
        model = Interruptores
        exclude = ['deleted']


class MedicionesInterruptoresSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicionesInterruptores
        fields = '__all__'
