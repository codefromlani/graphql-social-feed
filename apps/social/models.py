# apps/social/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone

class Follow(models.Model):
    id = models.BigAutoField(primary_key=True)

    follower = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="following")
    followed = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="followers")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "follows"
        constraints = [
            models.UniqueConstraint(fields=["follower", "followed"], name="unique_follow"),
            models.CheckConstraint(check=~models.Q(follower=models.F('followed')), name="prevent_self_follow")
        ]
        indexes = [
            models.Index(fields=["follower"]),
            models.Index(fields=["followed"]),
        ]

    def __str__(self):
        return f"{self.follower_id} -> {self.followed_id}"
