from django.contrib import admin

from .models import Manutencao


@admin.register(Manutencao)
class ManutencaoAdmin(admin.ModelAdmin):
    list_display = ("id", "sensor", "data_manutencao", "responsavel")
    list_filter = ("data_manutencao",)
    search_fields = ("responsavel", "descricao")
