import graphene
from apps.accounts.schema import AuthQuery, AuthMutations
from apps.posts.schema import Query as PostsQuery, PostMutations


class Query(AuthQuery, PostsQuery, graphene.ObjectType):
    pass


class Mutation(AuthMutations, PostMutations, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
