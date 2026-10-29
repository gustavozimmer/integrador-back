"""
Helpers de documentação OpenAPI (drf-spectacular).

Concentra respostas de erro padronizadas e um gerador de documentação para
ViewSets CRUD, evitando repetir os mesmos blocos em cada view.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers


class ErroDetalheSerializer(serializers.Serializer):
    """Formato padrão de erro do DRF para 401, 403 e 404."""

    detail = serializers.CharField(help_text="Mensagem descrevendo o erro.")


RESP_400 = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description=(
        "Dados inválidos. O corpo é um objeto no qual cada chave é o nome do "
        "campo (ou parâmetro) com problema e o valor é a lista de mensagens."
    ),
    examples=[
        OpenApiExample(
            "Erro de validação",
            value={"campo": ["Mensagem explicando o problema."]},
            response_only=True,
            status_codes=["400"],
        )
    ],
)

RESP_401 = OpenApiResponse(
    response=ErroDetalheSerializer,
    description="Token JWT ausente, inválido ou expirado.",
    examples=[
        OpenApiExample(
            "Não autenticado",
            value={"detail": "Authentication credentials were not provided."},
            response_only=True,
            status_codes=["401"],
        )
    ],
)

RESP_403 = OpenApiResponse(
    response=ErroDetalheSerializer,
    description=(
        "Sem permissão. Leitura (GET) é liberada a qualquer usuário "
        "autenticado; criar, alterar e excluir exige perfil de administrador."
    ),
    examples=[
        OpenApiExample(
            "Sem permissão",
            value={"detail": "You do not have permission to perform this action."},
            response_only=True,
            status_codes=["403"],
        )
    ],
)

RESP_404 = OpenApiResponse(
    response=ErroDetalheSerializer,
    description="Registro não encontrado.",
    examples=[
        OpenApiExample(
            "Não encontrado",
            value={"detail": "No Local matches the given query."},
            response_only=True,
            status_codes=["404"],
        )
    ],
)

PARAM_ID = OpenApiParameter(
    "id",
    OpenApiTypes.INT,
    OpenApiParameter.PATH,
    description="Identificador numérico do registro.",
)

PARAM_IS_ACTIVE = OpenApiParameter(
    "is_active",
    OpenApiTypes.BOOL,
    OpenApiParameter.QUERY,
    required=False,
    description=(
        "Filtra pela situação do registro: `true` (ativos) ou `false` "
        "(inativos). Sem o parâmetro, retorna todos. Qualquer outro valor "
        "resulta em erro 400."
    ),
)


def documentar_crud(
    *,
    tag,
    serializer,
    singular,
    plural,
    exclusao,
    parametros_listagem=None,
    exemplo_requisicao=None,
    exemplo_resposta=None,
    descricao_listagem="",
):
    """
    Gera a documentação das 6 ações de um ModelViewSet.

    `exclusao` descreve o que o DELETE faz (desativação lógica ou remoção).
    `exemplo_requisicao` / `exemplo_resposta` são dicionários opcionais usados
    como exemplos no Swagger.
    """
    exemplos_req = []
    exemplos_resp = []

    if exemplo_requisicao:
        exemplos_req.append(
            OpenApiExample(
                f"Exemplo de {singular}", value=exemplo_requisicao, request_only=True
            )
        )
    if exemplo_resposta:
        exemplos_resp.append(
            OpenApiExample(
                f"Exemplo de {singular}", value=exemplo_resposta, response_only=True
            )
        )

    erros_leitura = {401: RESP_401, 403: RESP_403}
    erros_escrita = {400: RESP_400, 401: RESP_401, 403: RESP_403}
    erros_item = {401: RESP_401, 403: RESP_403, 404: RESP_404}

    def resp(codigo, descricao):
        return OpenApiResponse(
            response=serializer, description=descricao, examples=exemplos_resp
        )

    return extend_schema_view(
        list=extend_schema(
            tags=[tag],
            summary=f"Listar {plural}",
            description=descricao_listagem or f"Retorna a lista de {plural}.",
            parameters=parametros_listagem or [],
            responses={200: serializer, **({400: RESP_400} if parametros_listagem else {}), **erros_leitura},
        ),
        retrieve=extend_schema(
            tags=[tag],
            summary=f"Detalhar {singular}",
            description=f"Retorna os dados de um(a) {singular} pelo identificador.",
            parameters=[PARAM_ID],
            responses={200: resp(200, "Registro encontrado."), **erros_item},
        ),
        create=extend_schema(
            tags=[tag],
            summary=f"Cadastrar {singular}",
            description=(
                f"Cadastra um(a) novo(a) {singular}. Campos somente leitura "
                "(como `id`) são ignorados se enviados. A operação é "
                "registrada na auditoria."
            ),
            examples=exemplos_req,
            responses={201: resp(201, "Registro criado."), **erros_escrita},
        ),
        update=extend_schema(
            tags=[tag],
            summary=f"Substituir {singular}",
            description=(
                f"Atualiza **todos** os campos editáveis de um(a) {singular} "
                "(PUT). Para alterar apenas alguns campos, use PATCH."
            ),
            parameters=[PARAM_ID],
            examples=exemplos_req,
            responses={200: resp(200, "Registro atualizado."), **erros_escrita, 404: RESP_404},
        ),
        partial_update=extend_schema(
            tags=[tag],
            summary=f"Atualizar parcialmente {singular}",
            description=(
                f"Atualiza apenas os campos enviados de um(a) {singular} (PATCH)."
            ),
            parameters=[PARAM_ID],
            responses={200: resp(200, "Registro atualizado."), **erros_escrita, 404: RESP_404},
        ),
        destroy=extend_schema(
            tags=[tag],
            summary=f"Excluir {singular}",
            description=exclusao,
            parameters=[PARAM_ID],
            responses={
                204: OpenApiResponse(description="Operação concluída, sem corpo na resposta."),
                **erros_item,
            },
        ),
    )
