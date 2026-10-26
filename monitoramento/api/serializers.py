
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
    )

    class Meta:
        model = Usuario
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "email",
            "tipo_usuario",
            "foto_perfil",
            "senha",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        senha = validated_data.pop("senha")
        usuario = Usuario(**validated_data)
        usuario.set_password(senha)
        usuario.save()
        return usuario

    def update(self, instance, validated_data):
        senha = validated_data.pop("senha", None)

        for atributo, valor in validated_data.items():
            setattr(instance, atributo, valor)

        if senha:
            instance.set_password(senha)

        instance.save()
        return instance
    

class LocalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Local
        fields = [
            "id",
            "nome",
            "descricao",
            "is_active",
        ]
        read_only_fields = ["id"]

    def validate_nome(self, value):
        nome = value.strip()

        if not nome:
            raise serializers.ValidationError(
                "O nome do local não pode ser vazio."
            )

        queryset = Local.objects.filter(nome__iexact=nome)

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um local com esse nome."
            )

        return nome 
    
class ModeloEquipamentoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloEquipamento
        fields = [
            "id",
            "nome",
            "fabricante",
            "descricao",
        ]
        read_only_fields = ["id"]

    def validate_nome(self, value):
        nome = value.strip()

        if not nome:
            raise serializers.ValidationError(
                "O nome do modelo de equipamento não pode ser vazio."
            )

        queryset = ModeloEquipamento.objects.filter(
            nome__iexact=nome
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um modelo de equipamento com esse nome."
            )

        return nome

class MicrocontroladorSerializer(serializers.ModelSerializer):
    modelo_nome = serializers.CharField(
        source="modelo.nome",
        read_only=True,
    )

    local_nome = serializers.CharField(
        source="local.nome",
        read_only=True,
    )

    class Meta:
        model = Microcontrolador
        fields = [
            "id",
            "modelo",
            "modelo_nome",
            "local",
            "local_nome",
            "mac_address",
            "latitude",
            "longitude",
            "observacoes",
            "data_cadastro",
            "is_active",
        ]
        read_only_fields = [
            "id",
            "data_cadastro",
        ]

    def validate_mac_address(self, value):
        mac = value.strip().upper()

        import re

        if not re.fullmatch(
            r"(?:[0-9A-F]{2}:){5}[0-9A-F]{2}",
            mac,
        ):
            raise serializers.ValidationError(
                "O endereço MAC deve seguir o formato "
                "XX:XX:XX:XX:XX:XX."
            )

        queryset = Microcontrolador.objects.filter(
            mac_address__iexact=mac
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um microcontrolador com esse endereço MAC."
            )

        return mac

class ModeloSensorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ModeloSensor
        fields = [
            "id",
            "nome",
            "fabricante",
            "descricao",
        ]
        read_only_fields = ["id"]

    def validate_nome(self, value):
        nome = value.strip()

        if not nome:
            raise serializers.ValidationError(
                "O nome do modelo de sensor não pode ser vazio."
            )

        queryset = ModeloSensor.objects.filter(
            nome__iexact=nome
        )

        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise serializers.ValidationError(
                "Já existe um modelo de sensor com esse nome."
            )

        return nome 


class SensorSerializer(serializers.ModelSerializer):
    modelo_nome = serializers.CharField(
        source="modelo.nome",
        read_only=True,
    )

    microcontrolador_mac = serializers.CharField(
        source="microcontrolador.mac_address",
        read_only=True,
    )

    tipo_display = serializers.CharField(
        source="get_tipo_display",
        read_only=True,
    )

    unidade_medida_display = serializers.CharField(
        source="get_unidade_medida_display",
        read_only=True,
    )

    class Meta:
        model = Sensor
        fields = [
            "id",
            "modelo",
            "modelo_nome",
            "microcontrolador",
            "microcontrolador_mac",
            "tipo",
            "tipo_display",
            "unidade_medida",
            "unidade_medida_display",
            "is_active",
            "data_cadastro",
        ]
        read_only_fields = [
            "id",
            "data_cadastro",
        ]

    def validate(self, attrs):
        tipo = attrs.get(
            "tipo",
            getattr(self.instance, "tipo", None),
        )

        unidade = attrs.get(
            "unidade_medida",
            getattr(self.instance, "unidade_medida", None),
        )

        unidades_por_tipo = {
            "TEMP": "C",
            "UMID": "%",
            "LUMI": "LUX",
            "PASS": "UN",
        }

        if tipo and unidade:
            unidade_esperada = unidades_por_tipo.get(tipo)

            if unidade != unidade_esperada:
                raise serializers.ValidationError({
                    "unidade_medida": (
                        f"O tipo de sensor selecionado exige "
                        f"a unidade de medida '{unidade_esperada}'."
                    )
                })

        return attrs

class LeituraSerializer(serializers.ModelSerializer):
    sensor_tipo = serializers.CharField(
        source="sensor.get_tipo_display",
        read_only=True,
    )

    sensor_unidade = serializers.CharField(
        source="sensor.get_unidade_medida_display",
        read_only=True,
    )

    modelo_sensor_nome = serializers.CharField(
        source="sensor.modelo.nome",
        read_only=True,
    )

    microcontrolador_mac = serializers.CharField(
        source="sensor.microcontrolador.mac_address",
        read_only=True,
    )

    class Meta:
        model = Leitura
        fields = [
            "id",
            "sensor",
            "sensor_tipo",
            "sensor_unidade",
            "modelo_sensor_nome",
            "microcontrolador_mac",
            "valor",
            "data_hora",
            "criado_em",
        ]
        read_only_fields = [
            "id",
            "criado_em",
        ]
    def validate_sensor(self, sensor):
        if not sensor.is_active:
            raise serializers.ValidationError(
                "Não é possível registrar leituras de um sensor inativo."
            )

        if not sensor.microcontrolador.is_active:
            raise serializers.ValidationError(
                "Não é possível registrar leituras de um microcontrolador inativo."
            )

        return sensor
    

class AuditLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(
        source="user.username",
        read_only=True,
        default=None,
    )

    class Meta:
        model = AuditLog
        fields = [
            "id",
            "user",
            "username",
            "action",
            "model_name",
            "object_id",
            "object_repr",
            "changes",
            "timestamp",
            "ip_address",
            "request_method",
            "request_path",
        ]
        read_only_fields = fields
