
from django.contrib.auth import get_user_model
from rest_framework import serializers
from .models import *
from datetime import datetime, time
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

Usuario = get_user_model()


class UsuarioSerializer(serializers.ModelSerializer):
    senha = serializers.CharField(
        write_only=True,
        required=True,
        min_length=8,
        style={"input_type": "password"},
        help_text="Senha (mínimo 8 caracteres). Somente escrita: nunca é retornada. "
        "No PATCH, se omitida, a senha atual é mantida.",
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
        extra_kwargs = {
            'username': {'help_text': 'Nome de login único.'},
            'first_name': {'help_text': 'Primeiro nome.'},
            'last_name': {'help_text': 'Sobrenome.'},
            'email': {'help_text': 'E-mail do usuário.'},
            'tipo_usuario': {'help_text': 'Perfil: `ADMIN` (Administrador) ou `USER` (Usuário). Padrão: `USER`.'},
            'foto_perfil': {'help_text': 'Imagem de perfil (envio como arquivo, `multipart/form-data`). Opcional.'},
        }

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
        extra_kwargs = {
            'nome': {'help_text': 'Nome do local (até 100 caracteres, único sem diferenciar maiúsculas).'},
            'descricao': {'help_text': 'Descrição livre do local. Opcional.'},
            'is_active': {'help_text': 'Indica se o local está ativo. Padrão: `true`.'},
        }

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
        extra_kwargs = {
            'nome': {'help_text': 'Nome do modelo (até 100 caracteres, único sem diferenciar maiúsculas).'},
            'fabricante': {'help_text': 'Fabricante (até 100 caracteres). Opcional.'},
            'descricao': {'help_text': 'Descrição livre. Opcional.'},
        }

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
        extra_kwargs = {
            'modelo': {'help_text': 'Id do modelo de equipamento.'},
            'local': {'help_text': 'Id do local onde o microcontrolador está instalado.'},
            'mac_address': {'help_text': 'Endereço MAC no formato `XX:XX:XX:XX:XX:XX` (hexadecimal; convertido para maiúsculas). Único.'},
            'latitude': {'help_text': 'Latitude em graus decimais, de -90 a 90 (até 6 casas decimais).'},
            'longitude': {'help_text': 'Longitude em graus decimais, de -180 a 180 (até 6 casas decimais).'},
            'observacoes': {'help_text': 'Observações livres. Opcional.'},
            'is_active': {'help_text': 'Indica se está ativo. Padrão: `true`.'},
        }

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
        extra_kwargs = {
            'nome': {'help_text': 'Nome do modelo (até 100 caracteres, único sem diferenciar maiúsculas).'},
            'fabricante': {'help_text': 'Fabricante (até 100 caracteres). Opcional.'},
            'descricao': {'help_text': 'Descrição livre. Opcional.'},
        }

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
        extra_kwargs = {
            'modelo': {'help_text': 'Id do modelo de sensor.'},
            'microcontrolador': {'help_text': 'Id do microcontrolador ao qual o sensor está ligado.'},
            'tipo': {'help_text': 'Tipo de grandeza medida: `TEMP`, `UMID`, `LUMI` ou `PASS`.'},
            'unidade_medida': {'help_text': 'Unidade, que deve corresponder ao tipo: `TEMP`→`C`, `UMID`→`%`, `LUMI`→`LUX`, `PASS`→`UN`.'},
            'is_active': {'help_text': 'Indica se o sensor está ativo. Padrão: `true`.'},
        }

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
        extra_kwargs = {
            'sensor': {'help_text': 'Id do sensor. Deve estar ativo e pertencer a um microcontrolador ativo.'},
            'valor': {'help_text': 'Valor medido (até 12 dígitos, 4 casas decimais).'},
            'data_hora': {'help_text': 'Momento da medição, em ISO 8601 (ex.: `2026-10-29T13:30:00Z`).'},
        }
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
    

class ManutencaoSerializer(serializers.ModelSerializer):
    sensor_tipo = serializers.CharField(
        source="sensor.get_tipo_display",
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

    local_nome = serializers.CharField(
        source="sensor.microcontrolador.local.nome",
        read_only=True,
    )

    class Meta:
        model = Manutencao
        fields = [
            "id",
            "sensor",
            "sensor_tipo",
            "modelo_sensor_nome",
            "microcontrolador_mac",
            "local_nome",
            "data_manutencao",
            "descricao",
            "responsavel",
            "criado_em",
        ]
        read_only_fields = [
            "id",
            "criado_em",
        ]
        extra_kwargs = {
            "sensor": {"help_text": "Id do sensor que recebeu a intervenção."},
            "data_manutencao": {"help_text": "Data e hora da intervenção, em ISO 8601 (ex.: `2026-10-29T09:00:00Z`). Não pode estar no futuro."},
            "descricao": {"help_text": "Descrição do que foi feito (não pode ser vazia)."},
            "responsavel": {"help_text": "Nome de quem realizou a intervenção (até 150 caracteres)."},
        }

    def validate_data_manutencao(self, value):
        if value > timezone.now():
            raise serializers.ValidationError(
                "A data da manutenção não pode estar no futuro."
            )

        return value

    def validate_descricao(self, value):
        descricao = value.strip()

        if not descricao:
            raise serializers.ValidationError(
                "A descrição da manutenção não pode ser vazia."
            )

        return descricao

    def validate_responsavel(self, value):
        responsavel = value.strip()

        if not responsavel:
            raise serializers.ValidationError(
                "O responsável pela manutenção não pode ser vazio."
            )

        return responsavel


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
        extra_kwargs = {
            "user": {"help_text": "Id do usuário que executou a ação (nulo se removido)."},
            "action": {"help_text": "Ação: CREATE, UPDATE, DELETE, ACTIVATE ou DEACTIVATE."},
            "model_name": {"help_text": "Modelo afetado (ex.: `api.Sensor`)."},
            "object_id": {"help_text": "Id do objeto afetado."},
            "object_repr": {"help_text": "Representação textual do objeto no momento da ação."},
            "changes": {"help_text": "Detalhes da alteração (ex.: `{\"fields\": [\"nome\"]}`)."},
            "timestamp": {"help_text": "Data e hora do registro."},
            "ip_address": {"help_text": "IP de origem da requisição."},
            "request_method": {"help_text": "Método HTTP usado."},
            "request_path": {"help_text": "Caminho da requisição."},
        }

class DataOuDataHoraField(serializers.Field):
 
    default_error_messages = {
        "invalid": "Informe uma data (AAAA-MM-DD) ou uma data e hora no formato ISO 8601.",
    }
 
    def __init__(self, fim_do_dia=False, **kwargs):
        self.fim_do_dia = fim_do_dia
        super().__init__(**kwargs)
 
    def to_internal_value(self, data):
        valor = str(data).strip()
 
        try:
            apenas_data = parse_date(valor)
            valor_dt = None if apenas_data else parse_datetime(valor)
        except ValueError:
            self.fail("invalid")
 
        if apenas_data:
            hora = time.max if self.fim_do_dia else time.min
            resultado = datetime.combine(apenas_data, hora)
        elif valor_dt:
            resultado = valor_dt
        else:
            self.fail("invalid")
 
        if timezone.is_naive(resultado):
            resultado = timezone.make_aware(
                resultado, timezone.get_current_timezone()
            )
 
        return resultado
 
    def to_representation(self, value):
        return value.isoformat()
    
class ResumoPeriodoSerializer(serializers.Serializer):
    """Valida os parâmetros de query ?data_inicio=...&data_fim=..."""
 
    data_inicio = DataOuDataHoraField(required=False)
    data_fim = DataOuDataHoraField(required=False, fim_do_dia=True)
 
    def validate(self, attrs):
        inicio = attrs.get("data_inicio")
        fim = attrs.get("data_fim")
 
        if inicio and fim and inicio > fim:
            raise serializers.ValidationError({
                "data_fim": "A data final deve ser maior ou igual à data inicial."
            })
 
        return attrs

class ResumoSensorSerializer(serializers.Serializer):
    sensor = serializers.IntegerField()
    tipo = serializers.CharField()
    tipo_display = serializers.CharField()
    unidade_medida = serializers.CharField()
    unidade_medida_display = serializers.CharField()
    modelo_nome = serializers.CharField()
    microcontrolador_mac = serializers.CharField()
    data_inicio = serializers.DateTimeField(allow_null=True)
    data_fim = serializers.DateTimeField(allow_null=True)
    quantidade_leituras = serializers.IntegerField()
    valor_minimo = serializers.FloatField(allow_null=True)
    valor_maximo = serializers.FloatField(allow_null=True)
    valor_medio = serializers.FloatField(allow_null=True)