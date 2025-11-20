import graphene
from apps.accounts.schema import AuthQuery, AuthMutations


class Query(AuthQuery, graphene.ObjectType):
    pass


class Mutation(AuthMutations, graphene.ObjectType):
    pass


schema = graphene.Schema(query=Query, mutation=Mutation)
