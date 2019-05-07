from django.db import models
from django.db.models import BigIntegerField

from compass_graphql.lib.db.module import Module


class ModuleData(models.Model):
    module = models.ForeignKey(Module, on_delete=models.CASCADE, default=1, null=False, blank=False)
    normalizeddata_id = BigIntegerField(default=1, null=False, blank=False)

    class Meta:
        unique_together = ("module", "normalizeddata_id")
