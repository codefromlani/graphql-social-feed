import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.contrib.postgres.indexes import GinIndex
from django.contrib.postgres.search import SearchVectorField

class Post(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="posts")

    content = models.TextField()
    language = models.CharField(max_length=10, blank=True, null=True)

    is_private = models.BooleanField(default=False)
    visibility = models.CharField(max_length=20, default="public") # public / followers / private

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    # Threaded replies
    reply_to_post = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")

    # Full-text search vector
    search_vector = SearchVectorField(null=True)

    class Meta:
        indexes = [
            # Per-author timeline index
            models.Index(fields=["author", "-created_at"]),
            # Global timeline index
            models.Index(fields=["-created_at"]),
            # Full-text search index
            GinIndex(fields=["search_vector"]),
        ]

    def __str__(self):
        return f"Post({self.id}) by {self.author.username}"
    

class Comment(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="comments")
    content = models.TextField()

    parent_comment = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL, related_name="replies")

    created_at = models.DateTimeField(default=timezone.now)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["post", "-created_at"]),
            models.Index(fields=["author"]),
        ]

    def __str__(self):
        return f"Comment({self.id}) on Post({self.post_id})"
    

class Like(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="likes")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="likes")

    reaction = models.CharField(max_length=20, default="like")
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_like")
        ]
        indexes = [
            models.Index(fields=["post"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Like({self.user_id} → {self.post_id})"


class Share(models.Model):
    id = models.BigAutoField(primary_key=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="shares")
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name="shares")

    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["user", "post"], name="unique_share")
        ]
        indexes = [
            models.Index(fields=["post"]),
            models.Index(fields=["user"]),
        ]

    def __str__(self):
        return f"Share({self.user_id} → {self.post_id})"
