import graphene
from apps.accounts.schema import AuthQuery, AuthMutations
from apps.posts.schema import Query as PostsQuery, PostMutations
from apps.social.schema import FollowQuery, FollowMutations


class Query(AuthQuery, PostsQuery, FollowQuery, graphene.ObjectType):
    pass


class Mutation(AuthMutations, PostMutations, FollowMutations, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
