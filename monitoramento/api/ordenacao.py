"""
Ordenação das consultas (listagens).

Uso nas views:

    class LeituraViewSet(AuditMixin, OrdenacaoMixin, viewsets.ModelViewSet):
        campos_ordenacao = {"data_hora": "data_hora", "valor": "valor"}

Uso na requisição:

    GET /api/leituras/?ordering=-valor            (maior valor primeiro)
    GET /api/leituras/?ordering=sensor,-data_hora (por sensor, depois mais recente)

Sem o parâmetro `ordering`, vale a ordenação padrão de cada listagem.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter
from rest_framework.exceptions import ValidationError

PARAM_NAME = "ordering"


def parametro_ordenacao(campos, padrao):
    """Gera o parâmetro `ordering` da documentação OpenAPI de uma listagem."""
    opcoes = ", ".join(f"`{campo}`" for campo in campos)
    return OpenApiParameter(
        PARAM_NAME,
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        required=False,
        description=(
            f"Ordena o resultado. Campos aceitos: {opcoes}. Use o prefixo `-` "
            "para ordem decrescente e vírgula para combinar campos "
            "(ex.: `-valor,data_hora`). "
            f"Sem o parâmetro, a ordem padrão é `{padrao}`. Campo desconhecido "
            "resulta em erro 400."
        ),
    )


class OrdenacaoMixin:
    """
    Permite ordenar a listagem pelo parâmetro `ordering`.

    `campos_ordenacao` mapeia o nome público do campo (usado na URL) para o
    caminho no ORM, o que permite ordenar por campos de tabelas relacionadas
    (ex.: `"local_nome": "local__nome"`) sem expor a estrutura interna.
    """

    campos_ordenacao = {}

    def filter_queryset(self, queryset):
        queryset = super().filter_queryset(queryset)

        # Só a listagem é ordenável; detalhar/alterar/excluir ignoram o parâmetro.
        if getattr(self, "action", "list") != "list":
            return queryset

        criterios = self._ler_ordenacao()
        if not criterios:
            return queryset

        # `pk` como último critério mantém a ordem estável entre as requisições
        # quando há valores repetidos (importante para paginação).
        return queryset.order_by(*criterios, "pk")

    def _ler_ordenacao(self):
        bruto = self.request.query_params.get(PARAM_NAME, "")
        pedidos = [item.strip() for item in bruto.split(",") if item.strip()]

        criterios = []
        invalidos = []
        usados = set()

        for pedido in pedidos:
            decrescente = pedido.startswith("-")
            nome = pedido.lstrip("-")

            if nome not in self.campos_ordenacao:
                invalidos.append(nome or pedido)
                continue

            if nome in usados:
                continue
            usados.add(nome)

            caminho = self.campos_ordenacao[nome]
            criterios.append(f"-{caminho}" if decrescente else caminho)

        if invalidos:
            aceitos = ", ".join(self.campos_ordenacao)
            raise ValidationError({
                PARAM_NAME: (
                    f"Campo(s) inválido(s): {', '.join(invalidos)}. "
                    f"Use: {aceitos} (prefixo '-' para ordem decrescente)."
                )
            })

        return criterios
