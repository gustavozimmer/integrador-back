"""
Views de autenticação JWT.

São subclasses das views do simplejwt apenas para anexar a documentação
OpenAPI (tags, descrições e formatos de resposta) sem alterar o comportamento.
"""
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import serializers
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

TAG = "Autenticação"


class TokenParSerializer(serializers.Serializer):
    access = serializers.CharField(
        help_text="Token de acesso (curta duração, 25 min). Enviado no "
        "cabeçalho `Authorization: Bearer <access>`."
    )
    refresh = serializers.CharField(
        help_text="Token de renovação (12 h). Use em `/api/auth/refresh/`."
    )


class TokenAcessoSerializer(serializers.Serializer):
    access = serializers.CharField(help_text="Novo token de acesso.")


_ERRO_TOKEN = OpenApiResponse(
    response=OpenApiTypes.OBJECT,
    description="Token inválido ou expirado.",
    examples=[
        OpenApiExample(
            "Token inválido",
            value={
                "detail": "Token is invalid or expired",
                "code": "token_not_valid",
            },
            response_only=True,
            status_codes=["401"],
        )
    ],
)


@extend_schema_view(
    post=extend_schema(
        tags=[TAG],
        summary="Login (obter tokens JWT)",
        description=(
            "Autentica com `username` e `password` e retorna o par de tokens "
            "JWT. Use o `access` no botão **Authorize** do Swagger ou no "
            "cabeçalho `Authorization: Bearer <access>`."
        ),
        examples=[
            OpenApiExample(
                "Credenciais",
                value={"username": "admin", "password": "senha-segura"},
                request_only=True,
            )
        ],
        responses={
            200: TokenParSerializer,
            401: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Credenciais inválidas.",
                examples=[
                    OpenApiExample(
                        "Credenciais inválidas",
                        value={
                            "detail": "No active account found with the given credentials"
                        },
                        response_only=True,
                        status_codes=["401"],
                    )
                ],
            ),
        },
    )
)
class LoginView(TokenObtainPairView):
    pass


@extend_schema_view(
    post=extend_schema(
        tags=[TAG],
        summary="Renovar token de acesso",
        description="Troca um token `refresh` válido por um novo token `access`.",
        responses={200: TokenAcessoSerializer, 401: _ERRO_TOKEN},
    )
)
class RefreshView(TokenRefreshView):
    pass


@extend_schema_view(
    post=extend_schema(
        tags=[TAG],
        summary="Verificar token",
        description=(
            "Verifica se um token (access ou refresh) é válido. Retorna 200 "
            "com corpo vazio (`{}`) quando válido."
        ),
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Token válido (corpo vazio).",
            ),
            401: _ERRO_TOKEN,
        },
    )
)
class VerifyView(TokenVerifyView):
    pass
