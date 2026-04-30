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
from services.AlertaTransformadorEmail import AlertaTransformadorEmail
from services.InterruptorPotencia import InterruptorPotencia
from .models import (
    Alertas,
    Analisisaceitefisicoquimico,
    Analisisgasesdisueltos,
    MedicionesTransformadores,
    Transformadores,
    Interruptores,
    MedicionesInterruptores,
    AlertasInterruptores,
    Pronosticos,
    PronosticosTransformadores
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
    AlertasInterruptoresSerializer,
    PronosticosSerializer,
    PronosticosTransformadoresSerializer
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
                N_O = float(serializer.validated_data.get("numero_operaciones"))
                T_A = float(serializer.validated_data.get("tiempo_apertura_A"))
                T_C = float(serializer.validated_data.get("tiempo_cierre_A"))
                I_F = float(serializer.validated_data.get("corriente_falla"))
                R_C = float(serializer.validated_data.get("resistencia_contactos_R"))
                fecha_mantenimiento = request.data.get("fecha_mantenimiento")

                id_interruptor = serializer.validated_data.get("Interruptores_idInterruptores")
                id_interruptor_obj = Interruptores.objects.get(idinterruptores=id_interruptor)

                # Crear instancia de interruptor con los promedios calculados
                interruptor = InterruptorPotencia(N_O, T_A, T_C, I_F, R_C)
                I_DM, I_EE, I_M = interruptor.calcular_indices()

                medicion = MedicionesInterruptores.objects.get(pk=serializer.instance.pk)
                medicion.I_DM = round(I_DM, 2)
                medicion.I_EE = round(I_EE, 2)
                medicion.I_M = round(I_M, 2)
                medicion.save()

                # Generar alerta y enviar email si es necesario al usuario logueado
                usuario_email = request.user.correo if request.user.is_authenticated else None
                usuario_nombre = request.user.nombre if request.user.is_authenticated else None
                alerta = AlertaInterruptorEmail.generar_alerta_interruptor(I_M, id_interruptor_obj, usuario_email, usuario_nombre)

                # Guardar la alerta en la base de datos
                alerta_db = AlertasInterruptores.objects.create(
                    id_interruptor=id_interruptor_obj,
                    valor_medicion=f"{I_M:.2f}",
                    tipo_alerta=alerta["color_alerta"],
                    condicion=alerta["mensaje_condicion"],
                    recomendacion=alerta["recomendacion"],
                    fecha_mantenimiento=fecha_mantenimiento if fecha_mantenimiento else None
                )

                return Response(
                    {
                        "message": "Medición de interruptor registrada exitosamente.",
                        "data": serializer.data,
                        "I_DM": f"{I_DM:.2f}",
                        "I_EE": f"{I_EE:.2f}",
                        "I_M": f"{I_M:.2f}",
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


class MedicionesInterruptoresListView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):
        id_interruptor = request.query_params.get('idInterruptor')
        qs = MedicionesInterruptores.objects.all().order_by('-idMediciones_Interruptores')
        if id_interruptor:
            qs = qs.filter(Interruptores_idInterruptores=id_interruptor)
        serializer = MedicionesInterruptoresSerializer(qs, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class MedicionesInterruptoresByInterruptorView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, pk, *args, **kwargs):
        mediciones = MedicionesInterruptores.objects.filter(
            Interruptores_idInterruptores=pk
        ).order_by('-idMediciones_Interruptores')
        serializer = MedicionesInterruptoresSerializer(mediciones, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


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


####   PRONOSTICOS

class PronosticosCreateView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def post(self, request, *args, **kwargs):
        from services.PronosticoInterruptor import calcular_pmant, calcular_fecha_recomendada
        from datetime import date as date_type

        interruptor_id = request.data.get('interruptor')
        fecha_mantenimiento_str = request.data.get('fecha_mantenimiento')

        if not interruptor_id or not fecha_mantenimiento_str:
            return Response(
                {"error": "Debe proporcionar interruptor y fecha_mantenimiento."},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            interruptor_obj = Interruptores.objects.get(idinterruptores=interruptor_id)
        except Interruptores.DoesNotExist:
            return Response({"error": "Interruptor no encontrado."}, status=status.HTTP_404_NOT_FOUND)

        # Get last 2 measurements ordered newest first
        mediciones = list(
            MedicionesInterruptores.objects.filter(
                Interruptores_idInterruptores=interruptor_id
            ).order_by('-idMediciones_Interruptores')[:2]
        )

        if len(mediciones) == 0:
            return Response(
                {"error": "No hay mediciones registradas. Debe ingresar al menos una medición antes de generar un pronóstico."},
                status=status.HTTP_400_BAD_REQUEST
            )

        m_current = mediciones[0]
        i_dm = float(m_current.I_DM) if m_current.I_DM is not None else 0.0
        i_ee = float(m_current.I_EE) if m_current.I_EE is not None else 0.0
        i_m = float(m_current.I_M) if m_current.I_M is not None else 0.0

        if len(mediciones) == 1:
            # New equipment: treat previous IM as 0 (perfect condition)
            i_m_prev = 0.0
            pmant_prev = 0.0
        else:
            m_prev = mediciones[1]
            i_m_prev = float(m_prev.I_M) if m_prev.I_M is not None else 0.0
            last_pronostico = Pronosticos.objects.filter(
                interruptor=interruptor_obj
            ).order_by('-fecha_creacion').first()
            pmant_prev = float(last_pronostico.Pmant) if last_pronostico and last_pronostico.Pmant is not None else 0.0

        delta_im = i_m - i_m_prev

        try:
            fecha_mant = datetime.strptime(fecha_mantenimiento_str, '%Y-%m-%d').date()
        except ValueError:
            return Response({"error": "Formato de fecha inválido. Use YYYY-MM-DD."}, status=status.HTTP_400_BAD_REQUEST)

        hoy = date_type.today()
        meses_desde_mant = (hoy.year - fecha_mant.year) * 12 + (hoy.month - fecha_mant.month)

        ta = float(m_current.tiempo_apertura_A)
        tc = float(m_current.tiempo_cierre_A)
        no = float(m_current.numero_operaciones)
        if_ = float(m_current.corriente_falla)
        rc = float(m_current.resistencia_contactos_R)

        pmant = calcular_pmant(ta, tc, no, if_, rc, i_m_prev, pmant_prev, meses_desde_mant, delta_im)
        fecha_recomendada = calcular_fecha_recomendada(pmant, fecha_mant)

        try:
            pronostico = Pronosticos.objects.create(
                interruptor=interruptor_obj,
                fecha_mantenimiento=fecha_mant,
                I_DM=round(i_dm, 4),
                I_EE=round(i_ee, 4),
                I_M=round(i_m, 4),
                I_M_prev=round(i_m_prev, 4),
                delta_IM=round(delta_im, 4),
                Pmant=round(pmant, 4),
                fecha_recomendada=fecha_recomendada,
            )
            return Response(
                {
                    "message": "Pronóstico registrado exitosamente.",
                    "data": {
                        "idpronostico": pronostico.idpronostico,
                        "I_DM": round(i_dm, 4),
                        "I_EE": round(i_ee, 4),
                        "I_M": round(i_m, 4),
                        "I_M_prev": round(i_m_prev, 4),
                        "delta_IM": round(delta_im, 4),
                        "Pmant": round(pmant * 100, 2),
                        "fecha_mantenimiento": fecha_mantenimiento_str,
                        "fecha_recomendada": fecha_recomendada.strftime('%Y-%m-%d'),
                    }
                },
                status=status.HTTP_201_CREATED
            )
        except Exception as e:
            return Response(
                {"message": "Ocurrió un error al guardar el pronóstico.", "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PronosticosListView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):
        pronosticos = []
        id_interruptor = request.query_params.get('idInterruptor')
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')

        filters = Q()

        if id_interruptor:
            filters &= Q(interruptor=id_interruptor)

        if fecha_desde and fecha_hasta:
            filters &= Q(fecha_creacion__range=[fecha_desde, fecha_hasta])
        elif fecha_desde:
            filters &= Q(fecha_creacion__gte=fecha_desde)
        elif fecha_hasta:
            filters &= Q(fecha_creacion__lte=fecha_hasta)

        queryset = Pronosticos.objects.filter(filters).order_by('-fecha_creacion')
        pronosticos_serializados = PronosticosSerializer(queryset, many=True).data

        for pronostico in pronosticos_serializados:
            equipo_data = None
            if pronostico['interruptor']:
                try:
                    interruptor = Interruptores.objects.get(idinterruptores=pronostico['interruptor'])
                    equipo_data = InterruptoresSerializer(interruptor).data
                except Interruptores.DoesNotExist:
                    pass

            pronosticos.append({
                "pronostico": pronostico,
                "equipo": equipo_data
            })

        return Response(pronosticos, status=status.HTTP_200_OK)


####   PRONOSTICOS TRANSFORMADORES

class PronosticosTransformadoresCreateView(APIView):
    """
    Vista para crear pronósticos de transformadores.
    Calcula HI, RM y fechas de mantenimiento.
    """
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def post(self, request, *args, **kwargs):
        serializer = PronosticosTransformadoresSerializer(data=request.data)
        if serializer.is_valid():
            try:
                pronostico = serializer.save()

                return Response(
                    {
                        "message": "Pronóstico de transformador registrado exitosamente.",
                        "data": PronosticosTransformadoresSerializer(pronostico).data,
                        "resumen": {
                            "hi_total": float(pronostico.hi_total) if pronostico.hi_total else None,
                            "rm_actual": float(pronostico.rm_actual) if pronostico.rm_actual else None,
                            "condicion": pronostico.condicion_hi,
                            "color_alerta": pronostico.color_alerta,
                            "fecha_optima_sugerida": pronostico.fecha_optima_sugerida.isoformat() if pronostico.fecha_optima_sugerida else None,
                            "criterio": pronostico.criterio_fecha,
                            "recomendacion": pronostico.recomendacion
                        }
                    },
                    status=status.HTTP_201_CREATED
                )
            except Exception as e:
                return Response(
                    {"message": "Ocurrió un error al guardar el pronóstico.", "error": str(e)},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class PronosticosTransformadoresListView(APIView):
    """
    Vista para listar pronósticos de transformadores.
    Soporta filtros por transformador y fechas.
    """
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, *args, **kwargs):
        pronosticos = []
        id_transformador = request.query_params.get('idTransformador')
        fecha_desde = request.query_params.get('fecha_desde')
        fecha_hasta = request.query_params.get('fecha_hasta')
        condicion = request.query_params.get('condicion')

        filters = Q()

        if id_transformador:
            filters &= Q(transformador=id_transformador)

        if condicion:
            filters &= Q(condicion_hi__icontains=condicion)

        if fecha_desde and fecha_hasta:
            filters &= Q(fecha_creacion__range=[fecha_desde, fecha_hasta])
        elif fecha_desde:
            filters &= Q(fecha_creacion__gte=fecha_desde)
        elif fecha_hasta:
            filters &= Q(fecha_creacion__lte=fecha_hasta)

        # Aplicar filtros
        queryset = PronosticosTransformadores.objects.filter(filters).order_by('-fecha_creacion')
        pronosticos_serializados = PronosticosTransformadoresSerializer(queryset, many=True).data

        # Añadir información del transformador
        for pronostico in pronosticos_serializados:
            transformador_data = None
            try:
                transformador = Transformadores.objects.get(idtransformadores=pronostico['transformador'])
                transformador_data = TransformadoresSerializer(transformador).data
            except Transformadores.DoesNotExist:
                transformador_data = None

            pronosticos.append({
                "pronostico": pronostico,
                "transformador": transformador_data
            })

        return Response(pronosticos, status=status.HTTP_200_OK)


class PronosticosTransformadoresDetailView(APIView):
    """
    Vista para obtener detalle de un pronóstico de transformador.
    """
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def get(self, request, pk, *args, **kwargs):
        try:
            pronostico = PronosticosTransformadores.objects.get(pk=pk)
        except PronosticosTransformadores.DoesNotExist:
            return Response(
                {"message": "El pronóstico especificado no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        pronostico_data = PronosticosTransformadoresSerializer(pronostico).data

        # Añadir información del transformador
        transformador_data = None
        try:
            transformador = Transformadores.objects.get(idtransformadores=pronostico.transformador_id)
            transformador_data = TransformadoresSerializer(transformador).data
        except Transformadores.DoesNotExist:
            pass

        return Response({
            "pronostico": pronostico_data,
            "transformador": transformador_data,
            "resumen": {
                "hi_funcional": float(pronostico.hi_funcional) if pronostico.hi_funcional else None,
                "hi_dielectrico": float(pronostico.hi_dielectrico) if pronostico.hi_dielectrico else None,
                "hi_total": float(pronostico.hi_total) if pronostico.hi_total else None,
                "estres_termico": float(pronostico.estres_termico) if pronostico.estres_termico else None,
                "rm_actual": float(pronostico.rm_actual) if pronostico.rm_actual else None,
                "condicion": pronostico.condicion_hi,
                "color_alerta": pronostico.color_alerta,
                "vida_util": pronostico.vida_util_remanente,
                "fecha_optima_sugerida": pronostico.fecha_optima_sugerida.isoformat() if pronostico.fecha_optima_sugerida else None,
                "fecha_programada": pronostico.fecha_programada.isoformat() if pronostico.fecha_programada else None,
                "criterio": pronostico.criterio_fecha,
                "recomendacion": pronostico.recomendacion
            }
        }, status=status.HTTP_200_OK)


class PronosticosTransformadoresEmailView(APIView):
    """
    Vista para enviar por correo la información de un pronóstico de transformador.
    """
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def post(self, request, pk, *args, **kwargs):
        try:
            pronostico = PronosticosTransformadores.objects.get(pk=pk)
        except PronosticosTransformadores.DoesNotExist:
            return Response(
                {"message": "El pronóstico especificado no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        # Obtener información del usuario logueado
        usuario_email = request.user.correo if request.user.is_authenticated else None
        usuario_nombre = request.user.nombre if request.user.is_authenticated else None

        if not usuario_email:
            return Response(
                {"message": "No se pudo obtener el correo del usuario."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Obtener datos del pronóstico
        pronostico_data = PronosticosTransformadoresSerializer(pronostico).data

        # Obtener nombre del transformador
        transformador_nombre = "N/A"
        try:
            transformador = Transformadores.objects.get(idtransformadores=pronostico.transformador_id)
            transformador_nombre = transformador.nombre
        except Transformadores.DoesNotExist:
            pass

        # Enviar email
        resultado = AlertaTransformadorEmail.enviar_pronostico_transformador(
            pronostico_data,
            transformador_nombre,
            usuario_email,
            usuario_nombre
        )

        if resultado["success"]:
            return Response(
                {"message": resultado["message"]},
                status=status.HTTP_200_OK
            )
        else:
            return Response(
                {"message": resultado["message"]},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PronosticosInterruptoresEmailView(APIView):
    permission_classes = [IsAuthenticated, IsTecnicoOrAdmin]

    def post(self, request, pk, *args, **kwargs):
        try:
            pronostico = Pronosticos.objects.get(pk=pk)
        except Pronosticos.DoesNotExist:
            return Response(
                {"message": "El pronóstico especificado no existe."},
                status=status.HTTP_404_NOT_FOUND
            )

        usuario_email = request.user.correo if request.user.is_authenticated else None
        usuario_nombre = request.user.nombre if request.user.is_authenticated else None

        if not usuario_email:
            return Response(
                {"message": "No se pudo obtener el correo del usuario."},
                status=status.HTTP_400_BAD_REQUEST
            )

        pronostico_data = PronosticosSerializer(pronostico).data

        interruptor_nombre = "N/A"
        try:
            interruptor = Interruptores.objects.get(idinterruptores=pronostico.interruptor_id)
            interruptor_nombre = interruptor.nombre
        except Interruptores.DoesNotExist:
            pass

        resultado = AlertaInterruptorEmail.enviar_pronostico_interruptor(
            pronostico_data,
            interruptor_nombre,
            usuario_email,
            usuario_nombre
        )

        if resultado["success"]:
            return Response({"message": resultado["message"]}, status=status.HTTP_200_OK)
        else:
            return Response({"message": resultado["message"]}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
