from django.contrib.auth import get_user_model
from rest_framework import viewsets, generics
from rest_framework.exceptions import NotFound
from rest_framework.pagination import PageNumberPagination
from rest_framework.parsers import MultiPartParser, FormParser
from django.utils.dateparse import parse_date
from rest_framework.exceptions import ValidationError
from .permissions import PerfilPermission
from .services import AuditMixin
from .ordenacao import OrdenacaoMixin, parametro_ordenacao
from .serializers import *
from .models import *
from django.db.models import Avg, Count, Max, Min
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiExample, OpenApiParameter, OpenApiResponse, extend_schema
from .docs import (
    PARAM_ID,
    PARAM_IS_ACTIVE,
    RESP_400,
    RESP_401,
    RESP_403,
    RESP_404,
    documentar_crud,
)

Usuario = get_user_model()


# Campos aceitos no parâmetro `ordering` de cada listagem
# (nome usado na URL -> caminho no ORM).
CAMPOS_ORDEM_USUARIO = {
    "id": "id",
    "username": "username",
    "first_name": "first_name",
    "last_name": "last_name",
    "email": "email",
    "tipo_usuario": "tipo_usuario",
}
CAMPOS_ORDEM_LOCAL = {"id": "id", "nome": "nome", "is_active": "is_active"}
CAMPOS_ORDEM_MODELO = {"id": "id", "nome": "nome", "fabricante": "fabricante"}
CAMPOS_ORDEM_MICROCONTROLADOR = {
    "id": "id",
    "mac_address": "mac_address",
    "modelo_nome": "modelo__nome",
    "local_nome": "local__nome",
    "data_cadastro": "data_cadastro",
    "is_active": "is_active",
}
CAMPOS_ORDEM_SENSOR = {
    "id": "id",
    "tipo": "tipo",
    "unidade_medida": "unidade_medida",
    "modelo_nome": "modelo__nome",
    "microcontrolador_mac": "microcontrolador__mac_address",
    "data_cadastro": "data_cadastro",
    "is_active": "is_active",
}
CAMPOS_ORDEM_LEITURA = {
    "id": "id",
    "data_hora": "data_hora",
    "valor": "valor",
    "sensor": "sensor_id",
    "criado_em": "criado_em",
}
CAMPOS_ORDEM_MANUTENCAO = {
    "id": "id",
    "data_manutencao": "data_manutencao",
    "responsavel": "responsavel",
    "sensor": "sensor_id",
    "local_nome": "sensor__microcontrolador__local__nome",
    "criado_em": "criado_em",
}
CAMPOS_ORDEM_AUDITORIA = {
    "timestamp": "timestamp",
    "action": "action",
    "model_name": "model_name",
    "user_id": "user_id",
    "id": "id",
}


@documentar_crud(
    tag="Usuários",
    serializer=UsuarioSerializer,
    singular="usuário",
    plural="usuários",
    parametros_listagem=[parametro_ordenacao(CAMPOS_ORDEM_USUARIO, "id")],
    descricao_listagem="Lista todos os usuários (por padrão ordenados por id). A senha nunca é retornada.",
    exclusao=(
        "Não remove o registro: **desativa** o usuário (`is_active=false`) e "
        "registra a ação na auditoria. Se já estiver inativo, nada muda."
    ),
    exemplo_requisicao={
        "username": "maria.silva",
        "first_name": "Maria",
        "last_name": "Silva",
        "email": "maria@exemplo.com",
        "tipo_usuario": "USER",
        "senha": "minimo8caracteres",
    },
    exemplo_resposta={
        "id": 3,
        "username": "maria.silva",
        "first_name": "Maria",
        "last_name": "Silva",
        "email": "maria@exemplo.com",
        "tipo_usuario": "USER",
        "foto_perfil": "http://localhost:8000/media/usuarios/foto.png",
    },
)
class UsuarioViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_USUARIO
    queryset = Usuario.objects.all().order_by("id")
    serializer_class = UsuarioSerializer
    permission_classes = [PerfilPermission]
    parser_classes = [MultiPartParser, FormParser]


@documentar_crud(
    tag="Locais",
    serializer=LocalSerializer,
    singular="local",
    plural="locais",
    parametros_listagem=[parametro_ordenacao(CAMPOS_ORDEM_LOCAL, "nome")],
    descricao_listagem="Lista os locais onde há microcontroladores instalados (por padrão, em ordem alfabética).",
    exclusao=(
        "**Desativa** o local (`is_active=false`) em vez de removê-lo, e "
        "registra a ação na auditoria."
    ),
    exemplo_requisicao={"nome": "Laboratório 1", "descricao": "Bloco A, térreo", "is_active": True},
    exemplo_resposta={"id": 1, "nome": "Laboratório 1", "descricao": "Bloco A, térreo", "is_active": True},
)
class LocalViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_LOCAL
    queryset = Local.objects.all()
    serializer_class = LocalSerializer
    permission_classes = [PerfilPermission]
    

@documentar_crud(
    tag="Modelos de equipamento",
    serializer=ModeloEquipamentoSerializer,
    singular="modelo de equipamento",
    plural="modelos de equipamento",
    parametros_listagem=[parametro_ordenacao(CAMPOS_ORDEM_MODELO, "nome")],
    exclusao=(
        "Remove o registro **definitivamente**. Não é possível excluir um "
        "modelo que ainda esteja vinculado a microcontroladores."
    ),
    exemplo_requisicao={"nome": "ESP32-WROOM", "fabricante": "Espressif", "descricao": "Microcontrolador com Wi-Fi e Bluetooth"},
    exemplo_resposta={"id": 1, "nome": "ESP32-WROOM", "fabricante": "Espressif", "descricao": "Microcontrolador com Wi-Fi e Bluetooth"},
)
class ModeloEquipamentoViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_MODELO
    queryset = ModeloEquipamento.objects.all()
    serializer_class = ModeloEquipamentoSerializer
    permission_classes = [PerfilPermission]


@documentar_crud(
    tag="Microcontroladores",
    serializer=MicrocontroladorSerializer,
    singular="microcontrolador",
    plural="microcontroladores",
    parametros_listagem=[PARAM_IS_ACTIVE, parametro_ordenacao(CAMPOS_ORDEM_MICROCONTROLADOR, "id")],
    descricao_listagem="Lista os microcontroladores, com filtro opcional por situação (`is_active`).",
    exclusao=(
        "**Desativa** o microcontrolador (`is_active=false`) em vez de removê-lo. "
        "Enquanto estiver inativo, não é possível registrar leituras de seus sensores."
    ),
    exemplo_requisicao={
        "modelo": 1,
        "local": 1,
        "mac_address": "A4:CF:12:9B:3E:01",
        "latitude": "-23.550520",
        "longitude": "-46.633308",
        "observacoes": "Instalado no teto",
        "is_active": True,
    },
    exemplo_resposta={
        "id": 1,
        "modelo": 1,
        "modelo_nome": "ESP32-WROOM",
        "local": 1,
        "local_nome": "Laboratório 1",
        "mac_address": "A4:CF:12:9B:3E:01",
        "latitude": "-23.550520",
        "longitude": "-46.633308",
        "observacoes": "Instalado no teto",
        "data_cadastro": "2026-10-29T13:30:00Z",
        "is_active": True,
    },
)
class MicrocontroladorViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_MICROCONTROLADOR
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


@documentar_crud(
    tag="Modelos de sensor",
    serializer=ModeloSensorSerializer,
    singular="modelo de sensor",
    plural="modelos de sensor",
    parametros_listagem=[parametro_ordenacao(CAMPOS_ORDEM_MODELO, "nome")],
    exclusao=(
        "Remove o registro **definitivamente**. Não é possível excluir um "
        "modelo que ainda esteja vinculado a sensores."
    ),
    exemplo_requisicao={"nome": "DHT22", "fabricante": "Aosong", "descricao": "Sensor de temperatura e umidade"},
    exemplo_resposta={"id": 1, "nome": "DHT22", "fabricante": "Aosong", "descricao": "Sensor de temperatura e umidade"},
)
class ModeloSensorViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_MODELO
    queryset = ModeloSensor.objects.all()
    serializer_class = ModeloSensorSerializer
    permission_classes = [PerfilPermission]

@documentar_crud(
    tag="Sensores",
    serializer=SensorSerializer,
    singular="sensor",
    plural="sensores",
    parametros_listagem=[PARAM_IS_ACTIVE, parametro_ordenacao(CAMPOS_ORDEM_SENSOR, "id")],
    descricao_listagem="Lista os sensores, com filtro opcional por situação (`is_active`).",
    exclusao=(
        "**Desativa** o sensor (`is_active=false`) em vez de removê-lo. "
        "Sensores inativos não aceitam novas leituras."
    ),
    exemplo_requisicao={
        "modelo": 1,
        "microcontrolador": 1,
        "tipo": "TEMP",
        "unidade_medida": "C",
        "is_active": True,
    },
    exemplo_resposta={
        "id": 1,
        "modelo": 1,
        "modelo_nome": "DHT22",
        "microcontrolador": 1,
        "microcontrolador_mac": "A4:CF:12:9B:3E:01",
        "tipo": "TEMP",
        "tipo_display": "Temperatura",
        "unidade_medida": "C",
        "unidade_medida_display": "Graus Celsius",
        "is_active": True,
        "data_cadastro": "2026-10-29T13:30:00Z",
    },
)
class SensorViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_SENSOR
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

@documentar_crud(
    tag="Leituras",
    serializer=LeituraSerializer,
    singular="leitura",
    plural="leituras",
    parametros_listagem=[
        OpenApiParameter("sensor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
                         description="Filtra pelo id do sensor."),
        OpenApiParameter("local", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
                         description="Filtra pelo id do local onde está o microcontrolador do sensor."),
        OpenApiParameter("data_inicio", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False,
                         description="Data inicial (inclusive), formato `AAAA-MM-DD`."),
        OpenApiParameter("data_fim", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False,
                         description="Data final (inclusive), formato `AAAA-MM-DD`. Não pode ser anterior a `data_inicio`."),
        parametro_ordenacao(CAMPOS_ORDEM_LEITURA, "-data_hora"),
    ],
    descricao_listagem=(
        "Lista as leituras. Por padrão, da mais recente para a mais antiga "
        "(`data_hora` decrescente); use `ordering` para ordenar por data da "
        "leitura, valor medido, sensor etc. Os filtros são combináveis. "
        "**Atenção:** a listagem não é paginada."
    ),
    exclusao="Remove a leitura **definitivamente** e registra a ação na auditoria.",
    exemplo_requisicao={"sensor": 1, "valor": "23.5000", "data_hora": "2026-10-29T13:30:00Z"},
    exemplo_resposta={
        "id": 100,
        "sensor": 1,
        "sensor_tipo": "Temperatura",
        "sensor_unidade": "Graus Celsius",
        "modelo_sensor_nome": "DHT22",
        "microcontrolador_mac": "A4:CF:12:9B:3E:01",
        "valor": "23.5000",
        "data_hora": "2026-10-29T13:30:00Z",
        "criado_em": "2026-10-29T13:30:02Z",
    },
)
class LeituraViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_LEITURA
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




@documentar_crud(
    tag="Manutenções",
    serializer=ManutencaoSerializer,
    singular="manutenção",
    plural="manutenções",
    parametros_listagem=[
        OpenApiParameter("sensor", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
                         description="Filtra pelo id do sensor."),
        OpenApiParameter("local", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
                         description="Filtra pelo id do local onde está o microcontrolador do sensor."),
        OpenApiParameter("responsavel", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
                         description="Filtra pelo nome do responsável (contém o texto, sem diferenciar maiúsculas)."),
        OpenApiParameter("data_inicio", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False,
                         description="Data inicial (inclusive), formato `AAAA-MM-DD`."),
        OpenApiParameter("data_fim", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False,
                         description="Data final (inclusive), formato `AAAA-MM-DD`. Não pode ser anterior a `data_inicio`."),
        parametro_ordenacao(CAMPOS_ORDEM_MANUTENCAO, "-data_manutencao"),
    ],
    descricao_listagem=(
        "Lista as intervenções registradas nos sensores. Por padrão, da mais "
        "recente para a mais antiga; use `ordering` para ordenar por data, "
        "responsável, sensor etc. Os filtros são combináveis. Para ver o "
        "histórico de um sensor, use `?sensor=<id>`."
    ),
    exclusao="Remove o registro de manutenção **definitivamente** e registra a ação na auditoria.",
    exemplo_requisicao={
        "sensor": 1,
        "data_manutencao": "2026-10-29T09:00:00Z",
        "descricao": "Substituição do sensor por desgaste e recalibração.",
        "responsavel": "João Pereira",
    },
    exemplo_resposta={
        "id": 1,
        "sensor": 1,
        "sensor_tipo": "Temperatura",
        "modelo_sensor_nome": "DHT22",
        "microcontrolador_mac": "A4:CF:12:9B:3E:01",
        "local_nome": "Laboratório 1",
        "data_manutencao": "2026-10-29T09:00:00Z",
        "descricao": "Substituição do sensor por desgaste e recalibração.",
        "responsavel": "João Pereira",
        "criado_em": "2026-10-29T13:45:10Z",
    },
)
class ManutencaoViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
    campos_ordenacao = CAMPOS_ORDEM_MANUTENCAO
    queryset = Manutencao.objects.select_related(
        "sensor",
        "sensor__modelo",
        "sensor__microcontrolador",
        "sensor__microcontrolador__local",
    ).all()

    serializer_class = ManutencaoSerializer
    permission_classes = [PerfilPermission]

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params

        sensor_id = params.get("sensor")
        local_id = params.get("local")
        responsavel = params.get("responsavel")
        data_inicio_raw = params.get("data_inicio")
        data_fim_raw = params.get("data_fim")

        if sensor_id:
            if not sensor_id.isdigit():
                raise ValidationError({
                    "sensor": "Informe um identificador numérico."
                })
            queryset = queryset.filter(sensor_id=int(sensor_id))

        if local_id:
            if not local_id.isdigit():
                raise ValidationError({
                    "local": "Informe um identificador numérico."
                })
            queryset = queryset.filter(
                sensor__microcontrolador__local_id=int(local_id)
            )

        if responsavel:
            queryset = queryset.filter(responsavel__icontains=responsavel)

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
            queryset = queryset.filter(data_manutencao__date__gte=data_inicio)

        if data_fim:
            queryset = queryset.filter(data_manutencao__date__lte=data_fim)

        return queryset.order_by("-data_manutencao")


class AuditLogPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = "page_size"
    max_page_size = 100


@extend_schema(
    tags=["Auditoria"],
    summary="Listar registros de auditoria",
    description=(
        "Histórico das operações de criação, alteração, ativação, desativação "
        "e exclusão feitas pela API, do mais recente para o mais antigo. "
        "Paginado (padrão: 10 por página, máximo 100). Somente leitura."
    ),
    parameters=[
        OpenApiParameter("user_id", OpenApiTypes.INT, OpenApiParameter.QUERY, required=False,
                         description="Filtra pelo id do usuário que executou a ação."),
        OpenApiParameter("action", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
                         enum=["CREATE", "UPDATE", "DELETE", "ACTIVATE", "DEACTIVATE"],
                         description="Tipo de ação."),
        OpenApiParameter("model_name", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
                         description="Modelo afetado, sem diferenciar maiúsculas (ex.: `api.Sensor`)."),
        OpenApiParameter("object_id", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
                         description="Id do objeto afetado."),
        OpenApiParameter("date_from", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False,
                         description="Data inicial (inclusive), formato `YYYY-MM-DD`."),
        OpenApiParameter("date_to", OpenApiTypes.DATE, OpenApiParameter.QUERY, required=False,
                         description="Data final (inclusive), formato `YYYY-MM-DD`. Deve ser igual ou posterior a `date_from`."),
        parametro_ordenacao(CAMPOS_ORDEM_AUDITORIA, "-timestamp"),
    ],
    responses={200: AuditLogSerializer, 400: RESP_400, 401: RESP_401, 403: RESP_403},
)
class AuditLogListView(OrdenacaoMixin, generics.ListAPIView):
    campos_ordenacao = CAMPOS_ORDEM_AUDITORIA
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

@extend_schema(
    tags=["Sensores"],
    summary="Resumo estatístico do sensor",
    description=(
        "Retorna a quantidade de leituras e os valores mínimo, máximo e médio "
        "(arredondados para 2 casas) de um sensor no período informado. Sem "
        "parâmetros, considera todas as leituras. Se não houver leituras no "
        "período, a quantidade é 0 e os valores são `null`."
    ),
    parameters=[
        OpenApiParameter("pk", OpenApiTypes.INT, OpenApiParameter.PATH, description="Id do sensor."),
        OpenApiParameter(
            "data_inicio", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
            description=(
                "Início do período. Aceita data (`AAAA-MM-DD`, considerada "
                "00:00:00) ou data e hora ISO 8601 (`2026-10-29T08:00:00Z`)."
            ),
        ),
        OpenApiParameter(
            "data_fim", OpenApiTypes.STR, OpenApiParameter.QUERY, required=False,
            description=(
                "Fim do período. Aceita data (`AAAA-MM-DD`, considerada até "
                "23:59:59.999999) ou data e hora ISO 8601. Não pode ser "
                "anterior a `data_inicio`."
            ),
        ),
    ],
    responses={
        200: OpenApiResponse(
            response=ResumoSensorSerializer,
            description="Resumo calculado.",
            examples=[
                OpenApiExample(
                    "Resumo",
                    value={
                        "sensor": 1,
                        "tipo": "TEMP",
                        "tipo_display": "Temperatura",
                        "unidade_medida": "C",
                        "unidade_medida_display": "Graus Celsius",
                        "modelo_nome": "DHT22",
                        "microcontrolador_mac": "A4:CF:12:9B:3E:01",
                        "data_inicio": "2026-10-01T00:00:00Z",
                        "data_fim": "2026-10-29T23:59:59.999999Z",
                        "quantidade_leituras": 1440,
                        "valor_minimo": 18.2,
                        "valor_maximo": 31.7,
                        "valor_medio": 24.85,
                    },
                    response_only=True,
                )
            ],
        ),
        400: RESP_400,
        401: RESP_401,
        403: RESP_403,
        404: RESP_404,
    },
)
class SensorResumoEstatisticoView(APIView):
    """
    GET /sensores/<id>/resumo/?data_inicio=...&data_fim=...
 
    Retorna quantidade de leituras, valor mínimo, máximo e médio do sensor
    no período informado. Os dois parâmetros são opcionais; sem eles, considera
    todas as leituras do sensor.
    """
 
    def get(self, request, pk):
        sensor = get_object_or_404(
            Sensor.objects.select_related("modelo", "microcontrolador"),
            pk=pk,
        )
 
        parametros = ResumoPeriodoSerializer(data=request.query_params)
        parametros.is_valid(raise_exception=True)
        inicio = parametros.validated_data.get("data_inicio")
        fim = parametros.validated_data.get("data_fim")
 
        leituras = Leitura.objects.filter(sensor=sensor)
 
        if inicio:
            leituras = leituras.filter(data_hora__gte=inicio)
 
        if fim:
            leituras = leituras.filter(data_hora__lte=fim)
 
        agregados = leituras.aggregate(
            quantidade=Count("id"),
            minimo=Min("valor"),
            maximo=Max("valor"),
            media=Avg("valor"),
        )
 
        def arredondar(numero):
            return None if numero is None else round(float(numero), 2)
 
        dados = {
            "sensor": sensor.pk,
            "tipo": sensor.tipo,
            "tipo_display": sensor.get_tipo_display(),
            "unidade_medida": sensor.unidade_medida,
            "unidade_medida_display": sensor.get_unidade_medida_display(),
            "modelo_nome": sensor.modelo.nome,
            "microcontrolador_mac": sensor.microcontrolador.mac_address,
            "data_inicio": inicio,
            "data_fim": fim,
            "quantidade_leituras": agregados["quantidade"],
            "valor_minimo": arredondar(agregados["minimo"]),
            "valor_maximo": arredondar(agregados["maximo"]),
            "valor_medio": arredondar(agregados["media"]),
        }
 
        return Response(ResumoSensorSerializer(dados).data)