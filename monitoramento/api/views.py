from django.contrib.auth import get_user_model
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from .serializers import *
from .models import *
Usuario = get_user_model()


class UsuarioViewSet(viewsets.ModelViewSet):
    queryset = Usuario.objects.all().order_by("id")
    serializer_class = UsuarioSerializer
    permission_classes = [IsAuthenticated]


class LocalViewSet(viewsets.ModelViewSet):
    queryset = Local.objects.all()
    serializer_class = LocalSerializer
    permission_classes = [IsAuthenticated]
    

class ModeloEquipamentoViewSet(viewsets.ModelViewSet):
    queryset = ModeloEquipamento.objects.all()
    serializer_class = ModeloEquipamentoSerializer
    permission_classes = [IsAuthenticated]


class MicrocontroladorViewSet(viewsets.ModelViewSet):
    queryset = Microcontrolador.objects.select_related("modelo", "local",).all()
    serializer_class = MicrocontroladorSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


class ModeloSensorViewSet(viewsets.ModelViewSet):
    queryset = ModeloSensor.objects.all()
    serializer_class = ModeloSensorSerializer
    permission_classes = [IsAuthenticated]

class SensorViewSet(viewsets.ModelViewSet):
    queryset = Sensor.objects.select_related("modelo", "microcontrolador",).all()
    serializer_class = SensorSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])

class LeituraViewSet(viewsets.ModelViewSet):
    queryset = Leitura.objects.select_related(
        "sensor",
        "sensor__modelo",
        "sensor__microcontrolador",
    ).all()

    serializer_class = LeituraSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = super().get_queryset()

        sensor_id = self.request.query_params.get("sensor")
        data_inicio = self.request.query_params.get("data_inicio")
        data_fim = self.request.query_params.get("data_fim")
        local_id = self.request.query_params.get("local")

        if sensor_id:
            queryset = queryset.filter(sensor_id=sensor_id)

        if data_inicio:
            queryset = queryset.filter(data_hora__gte=data_inicio)

        if data_fim:
            queryset = queryset.filter(data_hora__lte=data_fim)

        if local_id:
            queryset = queryset.filter(
                sensor__microcontrolador__local_id=local_id
            )

        return queryset
