import json
import os
from datetime import datetime

from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from services.AlertaInterruptorEmail import AlertaInterruptorEmail
from services.InterruptorPotencia import InterruptorPotencia
from .models import (
    Alertas,
    Analisisaceitefisicoquimico,
    Analisisgasesdisueltos,
    MedicionesTransformadores,
    Transformadores,
    Interruptores,
    AlertasInterruptores
)
from .permissions import IsAdmin, IsTecnicoOrAdmin
from .serializers import (
    AlertasSerializer,
    AnalisisAceiteFisicoQuimicoSerializer,
    AnalisisGasesDisueltosSerializer,
    LoginSerializer,
    TransformadoresSerializer,
    UsuarioSerializer,
    MedicionesTransformadoresSerializer,
    InterruptoresSerializer,
    MedicionesInterruptoresSerializer,
    AlertasInterruptoresSerializer
)

User = get_user_model()


###   USUARIOS

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        users = User.objects.all()
        serializer = UsuarioSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        print(request.data)
        serializer = UsuarioSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UsuarioDetailView(APIView):
    permission_classes = [IsAuthenticated, IsAdmin]

    def get(self, request, id):
        try:
            usuario = User.objects.get(idusuario=id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = UsuarioSerializer(usuario)
        return Response(serializer.data)

    def put(self, request, id):
        try:
            usuario = User.objects.get(idusuario=id)
        except User.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        serializer = UsuarioSerializer(usuario, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


####   MEDICIONES

class MedicionesCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def post(self, request, *args, **kwargs):
        serializer = MedicionesTransformadoresSerializer(data=request.data['info'])
        if serializer.is_valid():
            try:
                serializer.save()

                # Crear la carpeta si no existe
                ruta_carpeta = os.path.join(os.getcwd(), "mediciones", "transformadores")
                os.makedirs(ruta_carpeta, exist_ok=True)
                ruta_archivo = os.path.join(ruta_carpeta,
                                            f"medición_{serializer.data["idmediciones_transformadores"]}.json")

                with open(ruta_archivo, 'w', encoding='utf-8') as archivo_json:
                    json.dump(request.data['docs'], archivo_json, ensure_ascii=False, indent=4)

                return Response(
                    {
                        "message": "Medición registrada exitosamente.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"message": "Ocurrió un error al guardar los datos.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedicionesListView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):
        queryset = MedicionesTransformadores.objects.all().order_by('transformadores')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        id = request.query_params.get('id')

        if start_date != None and end_date != None:
            queryset = queryset.filter(fecha__range=[start_date, end_date])

        if id != None:
            queryset = queryset.filter(transformadores=id)

        if not queryset.exists():
            return Response(
                {"message": "No se encontraron mediciones para los valores especificados."},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = MedicionesTransformadoresSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MedicionesFilesView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, pk, *args, **kwargs):
        queryset = MedicionesTransformadores.objects.all().order_by('transformadores')
        # print(MedicionesTransformadoresSerializer(queryset, many=True))

        queryset = queryset.filter(idmediciones_transformadores=pk)

        ruta_archivo = os.path.join(os.getcwd(), "mediciones", "transformadores", f"medición_{pk}.json")
        if not os.path.exists(ruta_archivo):
            raise FileNotFoundError(f"El archivo no existe en la ruta: {ruta_archivo}")

        with open(ruta_archivo, 'r', encoding='utf-8') as archivo_json:
            info = json.load(archivo_json)

        if not queryset.exists():
            return Response(
                {"message": "No se encontraron archivos para los valores especificados."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(info, status=status.HTTP_200_OK)


class MedicionesOne(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, pk, *args, **kwargs):
        gases = Analisisgasesdisueltos.objects.get(mediciones_transformadores_idmediciones_transformadores=pk)
        aceites = Analisisaceitefisicoquimico.objects.get(mediciones_transformadores_idmediciones_transformadores=pk)
        gasesSerializer = AnalisisGasesDisueltosSerializer(gases)
        aceitesSerializer = AnalisisAceiteFisicoQuimicoSerializer(aceites)
        return Response({'gasesDisueltos': gasesSerializer.data, 'aceiteFisicoQuimico': aceitesSerializer.data},
                        status=status.HTTP_200_OK)


class MedicionesUpdateView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def put(self, request, pk, *args, **kwargs):
        try:
            medicion = MedicionesTransformadores.objects.get(pk=pk)
            gases = Analisisgasesdisueltos.objects.get(mediciones_transformadores_idmediciones_transformadores=pk)
            fisicoQuimico = Analisisaceitefisicoquimico.objects.get(
                mediciones_transformadores_idmediciones_transformadores=pk)
        except MedicionesTransformadores.DoesNotExist:
            return Response({"message": "La medición especificada no existe."}, status=status.HTTP_404_NOT_FOUND)
        except Analisisgasesdisueltos.DoesNotExist:
            return Response({"message": "El analisis de gases especificada no existe."},
                            status=status.HTTP_404_NOT_FOUND)
        except Analisisaceitefisicoquimico.DoesNotExist:
            return Response({"message": "El analisis de fisico quimico especificada no existe."},
                            status=status.HTTP_404_NOT_FOUND)

        try:
            serializer = MedicionesTransformadoresSerializer(medicion, data=request.data, partial=False)
            serializerGases = AnalisisGasesDisueltosSerializer(gases, data=request.data.get('analisis_gases_disueltos'),
                                                               partial=False)
            serializerFisicoQuimico = AnalisisAceiteFisicoQuimicoSerializer(fisicoQuimico, data=request.data.get(
                'analisis_aceite_fisico_quimico'), partial=False)
            if serializer.is_valid() and serializerGases.is_valid() and serializerFisicoQuimico.is_valid():
                serializer.save()
                serializerGases.save()
                serializerFisicoQuimico.save()
                return Response(
                    {"message": "Medición actualizada correctamente.", "data": serializer.data},
                    status=status.HTTP_200_OK
                )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al actualizar los datos.", "error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlertasListView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):

        alertas = []
        id_transformador = request.query_params.get('idTransformador')
        id_medicion = request.query_params.get('idMedicion')

        if id_transformador != None:
            queryset = MedicionesTransformadores.objects.filter(transformadores=id_transformador)


        elif id_medicion != None:
            queryset = MedicionesTransformadores.objects.filter(idmediciones_transformadores=id_medicion)

        else:
            queryset = MedicionesTransformadores.objects.all()

        medicion_temp = MedicionesTransformadoresSerializer(queryset, many=True).data

        for medicion in medicion_temp:
            alertas_queryset = Alertas.objects.filter(
                mediciones_transformadores=medicion['idmediciones_transformadores'])
            alertas_serializadas = AlertasSerializer(alertas_queryset, many=True).data

            if alertas_serializadas:  # Verificar si hay alertas asociadas
                alertas.append({
                    "alerta": alertas_serializadas[0],
                    "medicion": medicion
                })

        if len(alertas) == 0:
            return Response(
                {"message": "No se encontraron alertas para los valores especificados."},
                status=status.HTTP_404_NOT_FOUND
            )

        return Response(alertas, status=status.HTTP_200_OK)


class TranformadoresListView(APIView):
    permission_classes = [IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):
        queryset = Transformadores.objects.filter(deleted=False)
        serializer = TransformadoresSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = TransformadoresSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {
                        "message": "Transformador registrado exitosamente.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"message": "Ocurrió un error al guardar los datos.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class TransformadoresDetailView(APIView):
    permission_classes = [IsTecnicoOrAdmin]

    def get(self, request, pk, *args, **kwargs):
        transformador = get_object_or_404(Transformadores, pk=pk)
        serializer = TransformadoresSerializer(transformador)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        transformador = get_object_or_404(Transformadores, pk=pk)
        serializer = TransformadoresSerializer(transformador, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {
                        "message": "Transformador actualizado exitosamente.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"message": "Ocurrió un error al actualizar los datos.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        transformador = get_object_or_404(Transformadores, pk=pk)
        try:
            transformador.deleted = True  # Eliminación lógica (si aplicaste este sistema)
            transformador.save()
            return Response(
                {"message": "Transformador marcado como eliminado."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar el transformador.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class InterruptoresListView(APIView):
    permission_classes = [IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):
        queryset = Interruptores.objects.filter(deleted=False)
        serializer = InterruptoresSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request, *args, **kwargs):
        serializer = InterruptoresSerializer(data=request.data)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {
                        "message": "Interruptor registrado exitosamente.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"message": "Ocurrió un error al guardar los datos.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class InterruptoresDetailView(APIView):
    permission_classes = [IsTecnicoOrAdmin]

    def get(self, request, pk, *args, **kwargs):
        interruptor = get_object_or_404(Interruptores, pk=pk)
        serializer = InterruptoresSerializer(interruptor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk, *args, **kwargs):
        interruptor = get_object_or_404(Interruptores, pk=pk)
        serializer = InterruptoresSerializer(interruptor, data=request.data, partial=True)
        if serializer.is_valid():
            try:
                serializer.save()
                return Response(
                    {
                        "message": "Interruptor actualizado exitosamente.",
                        "data": serializer.data,
                    },
                    status=status.HTTP_200_OK
                )
            except Exception as e:
                return Response(
                    {"message": "Ocurrió un error al actualizar los datos.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk, *args, **kwargs):
        interruptor = get_object_or_404(Interruptores, pk=pk)
        try:
            interruptor.deleted = True
            interruptor.save()
            return Response(
                {"message": "Interruptor marcado como eliminado."},
                status=status.HTTP_200_OK
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al eliminar el interruptor.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class MedicionesInterruptoresCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def post(self, request, *args, **kwargs):
        serializer = MedicionesInterruptoresSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            try:
                # Obtener y validar los nuevos datos de apertura y cierre
                N_O = float(serializer.validated_data.get("numero_operaciones"))

                T_A_A = float(serializer.validated_data.get("tiempo_apertura_A"))
                T_A_B = float(serializer.validated_data.get("tiempo_apertura_B"))
                T_A_C = float(serializer.validated_data.get("tiempo_apertura_C"))

                T_C_A = float(serializer.validated_data.get("tiempo_cierre_A"))
                T_C_B = float(serializer.validated_data.get("tiempo_cierre_B"))
                T_C_C = float(serializer.validated_data.get("tiempo_cierre_C"))

                I_F = float(serializer.validated_data.get("corriente_falla"))

                R_C_R = float(serializer.validated_data.get("resistencia_contactos_R"))
                R_C_S = float(serializer.validated_data.get("resistencia_contactos_S"))
                R_C_T = float(serializer.validated_data.get("resistencia_contactos_T"))

                # Calcular promedio de resistencia de contactos
                R_C = (R_C_R + R_C_S + R_C_T) / 3

                id_interruptor = serializer.validated_data.get("Interruptores_idInterruptores")

                id_interruptor_obj = Interruptores.objects.get(idinterruptores=id_interruptor)

                # Calcular promedio de tiempos de apertura y cierre
                T_A = (T_A_A + T_A_B + T_A_C) / 3
                T_C = (T_C_A + T_C_B + T_C_C) / 3

                # Crear instancia de interruptor con los promedios calculados
                interruptor = InterruptorPotencia(N_O, T_A, T_C, I_F, R_C)
                _, _, I_M = interruptor.calcular_indices()

                # Generar alerta y enviar email si es necesario
                alerta = AlertaInterruptorEmail.generar_alerta_interruptor(I_M, id_interruptor_obj)

                # Guardar la alerta en la base de datos
                alerta_db = AlertasInterruptores.objects.create(
                    id_interruptor=id_interruptor_obj,
                    valor_medicion=f"{I_M:.2f}",
                    tipo_alerta=alerta["color_alerta"],
                    condicion=alerta["mensaje_condicion"],
                    recomendacion=alerta["recomendacion"],
                    fecha_medicion=datetime.now()
                )

                return Response(
                    {
                        "message": "Medición de interruptor registrada exitosamente.",
                        "data": serializer.data,
                        "valor_medicion": f"{I_M:.2f}",
                        "tipo_alerta": alerta["color_alerta"],
                        "condicion": alerta["mensaje_condicion"],
                        "id_alerta": alerta_db.id,
                        "fecha_medicion": alerta_db.fecha_medicion.strftime("%Y-%m-%d %H:%M:%S")
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"message": "Ocurrió un error al guardar los datos.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AlertasInterruptoresListView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):
        alertas = []
        id_interruptor = request.query_params.get('idInterruptor')
        tipo_alerta = request.query_params.get('tipo_alerta')
        condicion = request.query_params.get('condicion')
        fecha_inicio = request.query_params.get('fecha_inicio')
        fecha_fin = request.query_params.get('fecha_fin')

        filters = Q()

        if id_interruptor:
            filters &= Q(id_interruptor=id_interruptor)

        if tipo_alerta:
            filters &= Q(tipo_alerta__icontains=tipo_alerta)  # Búsqueda flexible

        if condicion:
            filters &= Q(condicion__icontains=condicion)  # Búsqueda flexible en texto

        if fecha_inicio and fecha_fin:
            filters &= Q(fecha_medicion__range=[fecha_inicio, fecha_fin])
        elif fecha_inicio:
            filters &= Q(fecha_medicion__gte=fecha_inicio)
        elif fecha_fin:
            filters &= Q(fecha_medicion__lte=fecha_fin)

        # Aplicar filtros
        queryset = AlertasInterruptores.objects.filter(filters)
        alertas_serializadas = AlertasInterruptoresSerializer(queryset, many=True).data

        # Añadir información del interruptor
        for alerta in alertas_serializadas:
            try:
                interruptor = Interruptores.objects.get(
                    idinterruptores=alerta['id_interruptor'])  # FIX: Campo corregido
                interruptor_serializado = InterruptoresSerializer(interruptor).data
            except Interruptores.DoesNotExist:
                interruptor_serializado = None  # Si el interruptor no existe, se devuelve None

            alertas.append({
                "alerta": alerta,
                "interruptor": interruptor_serializado
            })

        return Response(alertas, status=status.HTTP_200_OK)
