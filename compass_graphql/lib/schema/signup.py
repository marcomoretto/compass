import graphene
from django.contrib.auth.models import User
from graphene import Mutation
from graphene_django import DjangoObjectType


class UserType(DjangoObjectType):
    class Meta:

        model = User
        interfaces = (graphene.relay.Node,)


class Signup(Mutation):
    class Arguments:
        username = graphene.String(required=True)
        email = graphene.String(required=True)
        password = graphene.String(required=True)

    ok = graphene.Boolean()
    user = graphene.Field(UserType)

    def mutate(self, info, username, email, password):
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )
        return Signup(user=user, ok=True)

