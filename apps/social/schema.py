# apps/social/schema.py
import graphene
from graphene_django import DjangoObjectType
from graphql_jwt.decorators import login_required

from .models import Follow
from django.contrib.auth import get_user_model

from apps.accounts.schema import UserType

User = get_user_model()


class FollowType(DjangoObjectType):
    class Meta:
        model = Follow
        fields = ("id", "follower", "followed", "created_at")


class FollowMutations(graphene.ObjectType):
    follow_user = graphene.Field(FollowType, followed_id=graphene.UUID(required=True))
    unfollow_user = graphene.Field(graphene.Boolean, followed_id=graphene.UUID(required=True))

    @login_required
    def resolve_follow_user(self, info, followed_id):
        user = info.context.user
        if str(user.id) == str(followed_id):
            raise Exception("Cannot follow yourself")

        followed_user = User.objects.filter(id=followed_id).first()
        if not followed_user:
            raise Exception("User not found")

        follow, created = Follow.objects.get_or_create(follower=user, followed=followed_user)
        # return the follow object (created or existing)
        return follow

    @login_required
    def resolve_unfollow_user(self, info, followed_id):
        user = info.context.user
        deleted, _ = Follow.objects.filter(follower=user, followed_id=followed_id).delete()
        return deleted > 0


class FollowQuery(graphene.ObjectType):
    followers = graphene.List(UserType, user_id=graphene.UUID(required=True), limit=graphene.Int(), offset=graphene.Int())
    following = graphene.List(UserType, user_id=graphene.UUID(required=True), limit=graphene.Int(), offset=graphene.Int())
    follower_count = graphene.Int(user_id=graphene.UUID(required=True))
    following_count = graphene.Int(user_id=graphene.UUID(required=True))

    def resolve_followers(self, info, user_id, limit=50, offset=0):
        qs = User.objects.filter(following__followed_id=user_id).distinct().order_by("-id")
        return qs[offset: offset + limit]

    def resolve_following(self, info, user_id, limit=50, offset=0):
        qs = User.objects.filter(followers__follower_id=user_id).distinct().order_by("-id")
        return qs[offset: offset + limit]

    def resolve_follower_count(self, info, user_id):
        return Follow.objects.filter(followed_id=user_id).count()

    def resolve_following_count(self, info, user_id):
        return Follow.objects.filter(follower_id=user_id).count()
