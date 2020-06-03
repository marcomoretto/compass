import graphene
from graphene import ObjectType
import compass_graphql


class VersionType(ObjectType):

    version = graphene.String()


class Query(object):
    version = graphene.String()

    def resolve_version(self, info, **kwargs):
        return compass_graphql.__version__
