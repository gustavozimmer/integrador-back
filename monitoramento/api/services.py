
from .models import AuditLog


def register_audit(
    *,
    request,
    action,
    instance,
    changes=None,
):
    user = getattr(request, "user", None)

    if not user or not user.is_authenticated:
        user = None

    return AuditLog.objects.create(
        user=user,
        action=action,
        model_name=instance._meta.label,
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        changes=changes or {},
        ip_address=request.META.get("REMOTE_ADDR"),
        request_method=request.method,
        request_path=request.path[:500],
    )

from django.db import transaction

from .models import AuditLog
from .services import register_audit


class AuditMixin:

    def perform_create(self, serializer):
        with transaction.atomic():
            instance = serializer.save()

            register_audit(
                request=self.request,
                action=AuditLog.Action.CREATE,
                instance=instance,
                changes={
                    "fields": list(serializer.validated_data.keys()),
                },
            )

    def perform_update(self, serializer):
        instance = serializer.instance
        fields = list(serializer.validated_data.keys())

        with transaction.atomic():
            previous_active = getattr(instance, "is_active", None)

            instance = serializer.save()

            action = AuditLog.Action.UPDATE

            if "is_active" in fields:
                current_active = getattr(instance, "is_active", None)

                if previous_active is False and current_active is True:
                    action = AuditLog.Action.ACTIVATE

                elif previous_active is True and current_active is False:
                    action = AuditLog.Action.DEACTIVATE

            register_audit(
                request=self.request,
                action=action,
                instance=instance,
                changes={
                    "fields": fields,
                },
            )

    def perform_destroy(self, instance):
        with transaction.atomic():
            if hasattr(instance, "is_active"):
                if instance.is_active:
                    instance.is_active = False
                    instance.save(update_fields=["is_active"])

                    register_audit(
                        request=self.request,
                        action=AuditLog.Action.DEACTIVATE,
                        instance=instance,
                        changes={
                            "fields": ["is_active"],
                        },
                    )

                return

            register_audit(
                request=self.request,
                action=AuditLog.Action.DELETE,
                instance=instance,
            )

            instance.delete()
