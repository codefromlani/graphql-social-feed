# apps/posts/schema.py
import graphene
from graphene_django import DjangoObjectType
from django.conf import settings
from django.utils import timezone
from django.db.models import Q
from graphql_jwt.decorators import login_required

from .models import Post, Comment, Like, Share
from django.contrib.postgres.search import SearchQuery, SearchRank, SearchVector


# -------------------------
# Types
# -------------------------
class PostType(DjangoObjectType):
    class Meta:
        model = Post
        fields = ("id", "author", "content", "language", "is_private", "visibility", "created_at", "updated_at", "deleted_at", "reply_to_post", "replies", )


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = ("id", "post", "author", "content", "parent_comment", "created_at", "deleted_at")


class LikeType(DjangoObjectType):
    class Meta:
        model = Like
        fields = ("id", "user", "post", "reaction", "created_at")


class ShareType(DjangoObjectType):
    class Meta:
        model = Share
        fields = ("id", "user", "post", "created_at")


class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        fields = ("id", "post", "author", "content", "parent_comment", "created_at", "deleted_at",)


# -------------------------
# Input types
# -------------------------
class CreatePostInput(graphene.InputObjectType):
    content = graphene.String(required=True)
    language = graphene.String(required=False)
    is_private = graphene.Boolean(required=False)
    visibility = graphene.String(required=False)
    reply_to_post_id = graphene.UUID(required=False)


class UpdatePostInput(graphene.InputObjectType):
    post_id = graphene.UUID(required=True)
    content = graphene.String(required=False)
    language = graphene.String(required=False)
    is_private = graphene.Boolean(required=False)
    visibility = graphene.String(required=False)


class CreateCommentInput(graphene.InputObjectType):
    post_id = graphene.UUID(required=True)
    content = graphene.String(required=True)
    parent_comment_id = graphene.UUID(required=False)


# -------------------------
# Mutations
# -------------------------
class CreatePost(graphene.Mutation):
    post = graphene.Field(PostType)

    class Arguments:
        input = CreatePostInput(required=True)

    @login_required
    def mutate(self, info, input: CreatePostInput):
        user = info.context.user

        reply_to = None
        if input.reply_to_post_id:
            try:
                reply_to = Post.objects.get(id=input.reply_to_post_id, deleted_at__isnull=True)
            except Post.DoesNotExist:
                raise Exception("Reply-to post not found or deleted")

        post = Post.objects.create(
            author=user,
            content=input.content,
            language=input.language or None,
            is_private=input.is_private if input.is_private is not None else False,
            visibility=input.visibility or "public",
            reply_to_post=reply_to,
        )
        return CreatePost(post=post)
    

class UpdatePost(graphene.Mutation):
    post = graphene.Field(PostType)

    class Arguments:
        input = UpdatePostInput(required=True)

    @login_required
    def mutate(self, info, input: UpdatePostInput):
        user = info.context.user
        try:
            post = Post.objects.get(id=input.post_id, deleted_at__isnull=True)
        except Post.DoesNotExist:
            raise Exception("Post not found or deleted")

        if post.author_id != user.id and not user.is_staff:
            raise Exception("Permission denied")

        if input.content is not None:
            post.content = input.content
        if input.language is not None:
            post.language = input.language
        if input.is_private is not None:
            post.is_private = input.is_private
        if input.visibility is not None:
            post.visibility = input.visibility

        post.updated_at = timezone.now()
        post.save()
        return UpdatePost(post=post)
    

class DeletePost(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        post_id = graphene.UUID(required=True)

    @login_required
    def mutate(self, info, post_id):
        user = info.context.user
        try:
            post = Post.objects.get(id=post_id, deleted_at__isnull=True)
        except Post.DoesNotExist:
            raise Exception("Post not found or already deleted")

        if post.author_id != user.id and not user.is_staff:
            raise Exception("Permission denied")

        post.deleted_at = timezone.now()  # soft delete
        post.save()
        return DeletePost(ok=True)
    

class LikePost(graphene.Mutation):
    like = graphene.Field(LikeType)

    class Arguments:
        post_id = graphene.UUID(required=True)
        reaction = graphene.String(required=False)

    @login_required
    def mutate(self, info, post_id, reaction=None):
        user = info.context.user
        try:
            post = Post.objects.get(id=post_id, deleted_at__isnull=True)
        except Post.DoesNotExist:
            raise Exception("Post not found")

        # Upsert behavior - create if not exists
        like, created = Like.objects.get_or_create(user=user, post=post, defaults={"reaction": reaction or "like"})
        if not created:
            # update reaction timestamp & reaction if different
            if reaction and like.reaction != reaction:
                like.reaction = reaction
            like.created_at = timezone.now()
            like.save()
        return LikePost(like=like)
    

class UnlikePost(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        post_id = graphene.UUID(required=True)

    @login_required
    def mutate(self, info, post_id):
        user = info.context.user
        deleted, _ = Like.objects.filter(user=user, post_id=post_id).delete()
        return UnlikePost(ok=deleted > 0)
    

class SharePost(graphene.Mutation):
    share = graphene.Field(ShareType)
    
    class Arguments:
        post_id = graphene.UUID(required=True)

    @login_required
    def mutate(self, info, post_id):
        user = info.context.user

        try:
            post = Post.objects.get(id=post_id, deleted_at__isnull=True)
        except Post.DoesNotExist:
            raise Exception("Post not found")
        
        share, created = Share.objects.get_or_create(user=user, post=post)

        if not created:
            # already shared → update timestamp
            share.created_at = timezone.now()
            share.save()

        return SharePost(share=share)
    

class UnsharePost(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        post_id = graphene.UUID(required=True)

    @login_required
    def mutate(self, info, post_id):
        user = info.context.user

        deleted, _ = Share.objects.filter(user=user, post_id=post_id).delete()

        return UnsharePost(ok=deleted > 0)


class CreateComment(graphene.Mutation):
    comment = graphene.Field(CommentType)

    class Arguments:
        input = CreateCommentInput(required=True)

    @login_required
    def mutate(self, info, input):
        user = info.context.user

        try:
            post = Post.objects.get(id=input.post_id, deleted_at__isnull=True)
        except Post.DoesNotExist:
            raise Exception("Post not found")

        parent = None
        if input.parent_comment_id:
            try:
                parent = Comment.objects.get(id=input.parent_comment_id, deleted_at__isnull=True)
            except Comment.DoesNotExist:
                raise Exception("Parent comment not found")

        comment = Comment.objects.create(
            post=post,
            author=user,
            content=input.content,
            parent_comment=parent,
        )

        return CreateComment(comment=comment)
    

class DeleteComment(graphene.Mutation):
    ok = graphene.Boolean()

    class Arguments:
        comment_id = graphene.UUID(required=True)

    @login_required
    def mutate(self, info, comment_id):
        user = info.context.user

        try:
            comment = Comment.objects.get(id=comment_id, deleted_at__isnull=True)
        except Comment.DoesNotExist:
            raise Exception("Comment not found or already deleted")

        if comment.author_id != user.id and not user.is_staff:
            raise Exception("Permission denied")

        comment.deleted_at = timezone.now()
        comment.save()

        return DeleteComment(ok=True)


# Wrap all post mutations into a single object for schema import
class PostMutations(graphene.ObjectType):
    create_post = CreatePost.Field()
    update_post = UpdatePost.Field()
    delete_post = DeletePost.Field()
    like_post = LikePost.Field()
    unlike_post = UnlikePost.Field()
    share_post = SharePost.Field()
    unshare_post = UnsharePost.Field()
    create_comment = CreateComment.Field()
    delete_comment = DeleteComment.Field()

# -------------------------
# Queries
# -------------------------
class PostPage(graphene.ObjectType):
    items = graphene.List(PostType)
    has_next = graphene.Boolean()
    total = graphene.Int()


class Query(graphene.ObjectType):
    post = graphene.Field(PostType, id=graphene.UUID(required=True))
    global_feed = graphene.Field(PostPage, limit=graphene.Int(), offset=graphene.Int())
    author_feed = graphene.Field(PostPage, author_id=graphene.UUID(required=True), limit=graphene.Int(), offset=graphene.Int())
    replies = graphene.List(PostType, post_id=graphene.UUID(required=True))
    shares = graphene.List(ShareType, post_id=graphene.UUID(required=True))
    share_count = graphene.Int(post_id=graphene.UUID(required=True))
    comments = graphene.List(CommentType, post_id=graphene.UUID(required=True))
    comment_replies = graphene.List(CommentType, comment_id=graphene.UUID(required=True))
    comment_count = graphene.Int(post_id=graphene.UUID(required=True))


    def resolve_post(self, info, id):
        try:
            return Post.objects.get(id=id, deleted_at__isnull=True)
        except Post.DoesNotExist:
            return None
        
    def resolve_global_feed(self, info, limit=20, offset=0):
        qs = Post.objects.filter(deleted_at__isnull=True).order_by("-created_at")
        total = qs.count()
        items = qs[offset : offset + limit]
        has_next = offset + limit < total
        return PostPage(items=items, has_next=has_next, total=total)
        
    def resolve_author_feed(self, info, author_id, limit=20, offset=0):
        qs = Post.objects.filter(author_id=author_id, deleted_at__isnull=True).order_by("-created_at")
        total = qs.count()
        items = qs[offset : offset + limit]
        has_next = offset + limit < total
        return PostPage(items=items, has_next=has_next, total=total)
    
    def resolve_replies(self, info, post_id):
        return Post.objects.filter(reply_to_post_id=post_id, deleted_at__isnull=True).order_by("created_at")
    
    def resolve_shares(self, info, post_id):
        return Share.objects.filter(post_id=post_id)

    def resolve_share_count(self, info, post_id):
        return Share.objects.filter(post_id=post_id).count()
    
    def resolve_comments(self, info, post_id):
        return Comment.objects.filter(post_id=post_id, parent_comment__isnull=True, deleted_at__isnull=True).order_by("-created_at")

    def resolve_comment_replies(self, info, comment_id):
        return Comment.objects.filter(parent_comment_id=comment_id, deleted_at__isnull=True).order_by("created_at")

    def resolve_comment_count(self, info, post_id):
        return Comment.objects.filter(post_id=post_id, deleted_at__isnull=True).count()

    
# -------------------------
# Export schema fragment
# -------------------------
posts_schema = graphene.Schema(query=Query, mutation=PostMutations)
