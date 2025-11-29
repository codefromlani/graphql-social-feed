import graphene
from graphene_django import DjangoObjectType
from django.contrib.auth import get_user_model
from graphql_jwt.utils import jwt_encode
from graphql_jwt import ObtainJSONWebToken, Verify, Refresh

User = get_user_model()


# -----------------------------
# GraphQL Type for User
# -----------------------------
class UserType(DjangoObjectType):
    class Meta:
        model = User
        fields = ("id", "username", "email", "is_active")


# -----------------------------
# Signup Mutation
# -----------------------------
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
        # Convert UUID to string for JWT payload
        token = jwt_encode({"user_id": str(user.id)})
        return Signup(user=user, token=token)



# -----------------------------
# Root Mutation for Accounts
# -----------------------------
class AuthMutations(graphene.ObjectType):
    signup = Signup.Field()
    token_auth = ObtainJSONWebToken.Field()
    verify_token = Verify.Field()
    refresh_token = Refresh.Field()


# -----------------------------
# Auth-protected Query
# -----------------------------
class AuthQuery(graphene.ObjectType):
    me = graphene.Field(UserType)

    def resolve_me(self, info):
        user = info.context.user
        if user.is_anonymous:
            raise Exception("Authentication required")
        return user
