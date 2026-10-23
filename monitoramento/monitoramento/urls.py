from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
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

urlpatterns = [
    path('admin/', admin.site.urls),
    path("api/auth/login/", TokenObtainPairView.as_view(), name="token_obtain_pair",),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh",),
    path("api/auth/verify/", TokenVerifyView.as_view(), name="token_verify",),
    path('api/', include(router.urls)),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )