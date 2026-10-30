"""
Cria os usuários da avaliação em ambiente de desenvolvimento, um para cada perfil:

    python manage.py criar_usuarios_avaliacao

- Superusuário (Django):          lin / 123
- Administrador (tipo ADMIN):     senai.admin / 123456
- Usuário comum (tipo USER):      senai / 123456

As senhas são definidas direto (set_password), sem os validadores de senha do
Django nem o mínimo de 8 caracteres do serializer, que recusariam "123".
USE APENAS EM DESENVOLVIMENTO.

É idempotente: se o usuário já existir, senha e perfil são redefinidos.
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

Usuario = get_user_model()
Tipo = Usuario.TipoUsuario

USUARIOS = [
    # username, senha, superusuário, acessa o /admin/, tipo de usuário da API
    ("lin", "123", True, True, Tipo.ADMINISTRADOR),
    ("senai.admin", "123456", False, False, Tipo.ADMINISTRADOR),
    ("senai", "123456", False, False, Tipo.USUARIO),
]


class Command(BaseCommand):
    help = "Cria/atualiza o superusuário 'lin', o administrador 'senai.admin' e o usuário comum 'senai'."

    def handle(self, *args, **opcoes):
        for username, senha, is_superuser, is_staff, tipo in USUARIOS:
            usuario, criado = Usuario.objects.get_or_create(username=username)
            usuario.is_superuser = is_superuser
            usuario.is_staff = is_staff
            usuario.is_active = True
            usuario.tipo_usuario = tipo
            usuario.set_password(senha)
            usuario.save()
            situacao = "criado" if criado else "atualizado"
            self.stdout.write(self.style.SUCCESS(f"Usuário '{username}' {situacao} ({tipo.label})."))
