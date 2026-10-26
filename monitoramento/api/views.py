from django.contrib.auth import get_user_model
from rest_framework import viewsets, generics
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from .permissions import PerfilPermission
from .services import AuditMixin
from .serializers import *
from .models import *
Usuario = get_user_model()


class UsuarioViewSet(AuditMixin,viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by("id")
    serializer_class = UsuarioSerializer
    permission_classes = [PerfilPermission]
    parser_classes = [MultiPartParser, FormParser]


class LocalViewSet(AuditMixin,viewsets.ModelViewSet):
    queryset = Local.objects.all()
    serializer_class = LocalSerializer
    permission_classes = [PerfilPermission]
    

class ModeloEquipamentoViewSet(AuditMixin,viewsets.ModelViewSet):
    queryset = ModeloEquipamento.objects.all()
    serializer_class = ModeloEquipamentoSerializer
    permission_classes = [PerfilPermission]


class MicrocontroladorViewSet(AuditMixin,viewsets.ModelViewSet):
    queryset = Microcontrolador.objects.select_related("modelo", "local",).all()
    serializer_class = MicrocontroladorSerializer
    permission_classes = [PerfilPermission]
    
    def get_queryset(self):
        queryset = super().get_queryset()

        is_active = self.request.query_params.get("is_active")

        if is_active is not None:
            if is_active.lower() not in ("true", "false"):
                raise ValidationError({
                    "is_active": "Informe true ou false."
                })

            queryset = queryset.filter(
                is_active=is_active.lower() == "true"
            )

        return queryset

    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class ModeloSensorViewSet(AuditMixin,viewsets.ModelViewSet):
    queryset = ModeloSensor.objects.all()
    serializer_class = ModeloSensorSerializer
    permission_classes = [PerfilPermission]

class SensorViewSet(AuditMixin,viewsets.ModelViewSet):
    queryset = Sensor.objects.select_related("modelo", "microcontrolador",).all()
    serializer_class = SensorSerializer
    permission_classes = [PerfilPermission]
    
    
    def get_queryset(self):
        queryset = super().get_queryset()

        is_active = self.request.query_params.get("is_active")

        if is_active is not None:
            if is_active.lower() not in ("true", "false"):
                raise ValidationError({
                    "is_active": "Informe true ou false."
                })

            queryset = queryset.filter(
                is_active=is_active.lower() == "true"
            )

        return queryset
        
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])

class LeituraViewSet(AuditMixin,viewsets.ModelViewSet):
    queryset = Leitura.objects.select_related(
        "sensor",
        "sensor__modelo",
        "sensor__microcontrolador",
    ).all()

    serializer_class = LeituraSerializer
    permission_classes = [PerfilPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        sensor_id = params.get("sensor")
        local_id = params.get("local")
        data_inicio_raw = params.get("data_inicio")
        data_fim_raw = params.get("data_fim")

        if sensor_id:
            queryset = queryset.filter(sensor_id=sensor_id)

        if local_id:
            queryset = queryset.filter(
                sensor__microcontrolador__local_id=local_id
            )

        data_inicio = None
        data_fim = None

        if data_inicio_raw:
            data_inicio = parse_date(data_inicio_raw)
            if data_inicio is None:
                raise ValidationError({
                    "data_inicio": "Use o formato AAAA-MM-DD."
                })

        if data_fim_raw:
            data_fim = parse_date(data_fim_raw)
            if data_fim is None:
                raise ValidationError({
                    "data_fim": "Use o formato AAAA-MM-DD."
                })

        if data_inicio and data_fim and data_inicio > data_fim:
            raise ValidationError({
                "periodo": "A data inicial não pode ser posterior à data final."
            })

        if data_inicio:
            queryset = queryset.filter(
                data_hora__date__gte=data_inicio
            )

        if data_fim:
            queryset = queryset.filter(
                data_hora__date__lte=data_fim
            )

        return queryset.order_by("-data_hora")


from rest_framework.permissions import BasePermission, SAFE_METHODS


class AuditLogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


class AuditLogListView(generics.ListAPIView):
    serializer_class = AuditLogSerializer
    permission_classes = [PerfilPermission]
    pagination_class = AuditLogPagination

    def get_queryset(self):
        queryset = AuditLog.objects.select_related(
            "user"
        ).order_by("-timestamp")

        params = self.request.query_params

        user_id = params.get("user_id")
        action = params.get("action")
        model_name = params.get("model_name")
        object_id = params.get("object_id")
        date_from = params.get("date_from")
        date_to = params.get("date_to")

        if user_id:
            if not user_id.isdigit():
                raise ValidationError({
                    "user_id": "Informe um identificador numérico."
                })
            queryset = queryset.filter(user_id=int(user_id))

        if action:
            valid_actions = AuditLog.Action.values

            if action not in valid_actions:
                raise ValidationError({
                    "action": "Ação de auditoria inválida."
                })

            queryset = queryset.filter(action=action)

        if model_name:
            queryset = queryset.filter(
                model_name__iexact=model_name
            )

        if object_id:
            queryset = queryset.filter(
                object_id=object_id
            )

        if date_from:
            parsed_date = parse_date(date_from)

            if parsed_date is None:
                raise ValidationError({
                    "date_from": "Use o formato YYYY-MM-DD."
                })

            queryset = queryset.filter(
                timestamp__date__gte=parsed_date
            )

        if date_to:
            parsed_date = parse_date(date_to)

            if parsed_date is None:
                raise ValidationError({
                    "date_to": "Use o formato YYYY-MM-DD."
                })

            queryset = queryset.filter(
                timestamp__date__lte=parsed_date
            )

        if date_from and date_to:
            if parse_date(date_from) > parse_date(date_to):
                raise ValidationError({
                    "date_to": "A data final deve ser igual ou posterior à inicial."
                })

        return queryset
