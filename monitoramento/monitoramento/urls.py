from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from api.auth_views import LoginView, RefreshView, VerifyView
from rest_framework.routers import DefaultRouter
from api.views import *

router = DefaultRouter()
router.register("usuarios", UsuarioViewSet, basename="usuario")
router.register("locais", LocalViewSet, basename="local")
router.register("modelos-equipamentos", ModeloEquipamentoViewSet, basename="modelo-equipamento",)
router.register("microcontroladores", MicrocontroladorViewSet, basename="microcontrolador",)
router.register("modelos-sensores", ModeloSensorViewSet, basename="modelo-sensor",)
router.register("sensores", SensorViewSet, basename="sensor",)
router.register("leituras", LeituraViewSet, basename="leitura",)
router.register("manutencoes", ManutencaoViewSet, basename="manutencao",)    

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/login/", LoginView.as_view(), name="token_obtain_pair",),
    path("api/auth/refresh/", RefreshView.as_view(), name="token_refresh",),
    path("api/auth/verify/", VerifyView.as_view(), name="token_verify",),
    path(
        "api/auditoria/",
        AuditLogListView.as_view(),
        name="audit-list",
    ),
    path(
        "api/sensores/<int:pk>/resumo/",
        SensorResumoEstatisticoView.as_view(),
        name="sensor-resumo",
    ),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )