# scripts/seed_data.py
import os
import django
import random
from datetime import timedelta
from django.utils import timezone

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "social_feed.settings")
django.setup()

from django.contrib.auth import get_user_model
from apps.posts.models import Post, Comment, Like, Share
from apps.social.models import Follow

User = get_user_model()

# ----------------------------
# 1. Create Users
# ----------------------------
users_data = [
    {"username": "alice", "email": "alice@mail.com", "password": "1234"},
    {"username": "bob", "email": "bob@mail.com", "password": "1234"},
    {"username": "carol", "email": "carol@mail.com", "password": "1234"},
    {"username": "dave", "email": "dave@mail.com", "password": "1234"},
]

users = []
for data in users_data:
    user, created = User.objects.get_or_create(username=data["username"], email=data["email"])
    if created:
        user.set_password(data["password"])
        user.save()
    users.append(user)

print(f"Created {len(users)} users")

# ----------------------------
# 2. Create Posts
# ----------------------------
posts = []
for i in range(10):
    author = random.choice(users)
    post = Post.objects.create(
        author=author,
        content=f"This is test post #{i+1} by {author.username}",
        visibility=random.choice(["public", "followers", "private"]),
        created_at=timezone.now() - timedelta(days=random.randint(0, 5))
    )
    posts.append(post)

print(f"Created {len(posts)} posts")

# ----------------------------
# 3. Create Comments (including replies)
# ----------------------------
comments = []
for post in posts:
    num_comments = random.randint(1, 3)
    for j in range(num_comments):
        author = random.choice(users)
        comment = Comment.objects.create(
            post=post,
            author=author,
            content=f"Comment {j+1} on {post.id} by {author.username}"
        )
        comments.append(comment)

# Add some replies to first comment of each post
for post in posts:
    if post.comments.exists():
        parent_comment = post.comments.first()
        reply_author = random.choice(users)
        reply = Comment.objects.create(
            post=post,
            author=reply_author,
            content=f"Reply to comment {parent_comment.id} by {reply_author.username}",
            parent_comment=parent_comment
        )
        comments.append(reply)

print(f"Created {len(comments)} comments (including replies)")

# ----------------------------
# 4. Create Likes
# ----------------------------
likes_count = 0
for post in posts:
    for user in users:
        if random.choice([True, False]):
            like, created = Like.objects.get_or_create(user=user, post=post)
            likes_count += 1

print(f"Created {likes_count} likes")

# ----------------------------
# 5. Create Shares
# ----------------------------
shares_count = 0
for post in posts:
    for user in users:
        if random.choice([True, False]):
            share, created = Share.objects.get_or_create(user=user, post=post)
            shares_count += 1

print(f"Created {shares_count} shares")

# ----------------------------
# 6. Create Follows
# ----------------------------
follows_count = 0
for user in users:
    others = [u for u in users if u != user]
    for target in others:
        if random.choice([True, False]):
            follow, created = Follow.objects.get_or_create(follower=user, followed=target)
            follows_count += 1

print(f"Created {follows_count} follow relationships")

print("✅ Seed data complete. Ready to test GraphQL API!")
