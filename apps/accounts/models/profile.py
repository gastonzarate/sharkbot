"""Profiles models"""

import uuid

from django.contrib.auth.models import User
from django.db import models

from core.models import TimeStampedModel


class Profile(TimeStampedModel):
    """This class is to save more info about users"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    def __str__(self):
        return self.user.username
