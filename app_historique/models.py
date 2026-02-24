from __future__ import annotations

from django.db import models
from app_contact.models import User


class HistoriqueRetentionSetting(models.Model):
    """
    Singleton (1 seule ligne) : durée de conservation en années.
    Exemple : 2 => conserver année courante et année précédente.
    """
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    retention_years = models.PositiveSmallIntegerField(default=2)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "historique_retention_setting"

    @classmethod
    def get_value(cls) -> int:
        obj, _ = cls.objects.get_or_create(id=1, defaults={"retention_years": 2})
        return int(obj.retention_years)


class HistoriqueUser(models.Model):
    ACTION_CREATE = "CREATE"
    ACTION_READ = "READ"
    ACTION_UPDATE = "UPDATE"
    ACTION_DELETE = "DELETE"

    ACTION_CHOICES = (
        (ACTION_CREATE, "CREATE"),
        (ACTION_READ, "READ"),
        (ACTION_UPDATE, "UPDATE"),
        (ACTION_DELETE, "DELETE"),
    )

    # ✅ IMPORTANT : user peut être NULL (visiteur non connecté)
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historiques_actions",
    )

    action = models.CharField(max_length=10, choices=ACTION_CHOICES, db_index=True)

    # Cible "générique"
    app_label = models.CharField(max_length=100, blank=True, default="", db_index=True)
    model_name = models.CharField(max_length=100, blank=True, default="", db_index=True)
    object_id = models.CharField(max_length=64, blank=True, default="")
    object_repr = models.CharField(max_length=255, blank=True, default="")

    # Date/heure séparées
    date_action = models.DateField(auto_now_add=True, db_index=True)
    heure_action = models.TimeField(auto_now_add=True)

    # Trace HTTP
    url = models.CharField(max_length=255, blank=True, default="")
    method = models.CharField(max_length=10, blank=True, default="")
    ip = models.GenericIPAddressField(null=True, blank=True)
    details = models.TextField(blank=True, default="")

    class Meta:
        db_table = "historique_user"
        ordering = ["-date_action", "-heure_action"]
        indexes = [
            models.Index(fields=["date_action"]),
            models.Index(fields=["action"]),
            models.Index(fields=["app_label", "model_name"]),
        ]

    def __str__(self) -> str:
        who = self.user.email if self.user else "non connecté"
        return f"[{self.action}] {who} - {self.app_label}.{self.model_name} - {self.object_repr}"
