import graphene
from django.conf import settings
from graphene import ObjectType
from graphene.types.resolver import dict_resolver

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class CompendiumType(ObjectType):

    class Meta:
        default_resolver = dict_resolver

    name = graphene.String()
    full_name = graphene.String()
    description = graphene.String()
    normalization = graphene.List(graphene.String)


class Query(object):
    compendia = graphene.List(CompendiumType)

    def resolve_compendia(self, info, **kwargs):
        compendia = []
        for k, db in settings.DATABASES.items():
            if db.get('COMPENDIUM', False):
                conf = CompendiumConfig(k)
                compendia.append({
                    'name': k,
                    'full_name': conf.get_full_name(),
                    'description': conf.get_description(),
                    'normalization': conf.get_normalization_names()
                })
        return compendia
