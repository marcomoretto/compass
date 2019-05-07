from django.contrib.auth.models import User
from django.db import models


class Module(models.Model):
    name = models.TextField()
    compendium_nick_name = models.TextField()
    user = models.ForeignKey(User)
    biological_features_num = models.IntegerField(default=0)
    sample_sets_num = models.IntegerField(default=0)

    class Meta:
        unique_together = ("name", "compendium_nick_name", "user")
