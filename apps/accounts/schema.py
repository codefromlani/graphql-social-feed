import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
import graphql_jwt

User = get_user_model()

# GraphQL Type
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active")


# Signup Mutation
class Signup(graphene.Mutation):
    user = graphene.Field(UserType)
    token = graphene.String()

    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    def mutate(self, info, username, email, password):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        # Generate JWT for new user
        token = graphql_jwt.shortcuts.get_token(user)
        return Signup(user=user, token=token)
    

# Root Mutation for Accounts
class AuthMutations(graphene.ObjectType):
    signup = Signup.Field()
    # Built-in JWT mutations:
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()


# Auth-protected Query
class AuthQuery(graphene.ObjectType):
    me = graphene.Field(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required")
        return user
