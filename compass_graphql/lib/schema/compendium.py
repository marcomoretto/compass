import graphene
from django.conf import settings
from graphene import ObjectType
from graphene.types.resolver import dict_resolver
import compass
import os
import glob

from compass_graphql.lib.utils.compendium_config import CompendiumConfig

class CompendiumDatabaseType(ObjectType):

    class Meta:
        default_resolver = dict_resolver

    name = graphene.Field(graphene.String)
    normalizations = graphene.List(graphene.String)


class CompendiumVersionType(ObjectType):

    class Meta:
        default_resolver = dict_resolver

    version_number = graphene.Field(graphene.String)
    version_alias = graphene.Field(graphene.String)
    databases = graphene.List(CompendiumDatabaseType)
    default_database = graphene.Field(graphene.String)


class CompendiumType(ObjectType):

    class Meta:
        default_resolver = dict_resolver

    name = graphene.Field(graphene.String)
    full_name = graphene.Field(graphene.String)
    description = graphene.Field(graphene.String)
    versions = graphene.List(CompendiumVersionType)
    default_version = graphene.Field(graphene.String)


class Query(object):
    compendia = graphene.List(CompendiumType)

    def resolve_compendia(self, info, **kwargs):
        cc = CompendiumConfig().compendia
        for c in cc:
            for v in c['versions']:
                for d in v['databases']:
                    norm = []
                    for n in d['normalizations']:
                        default = ''
                        if n['name'] == d['default_normalization']:
                            default = ' (default)'
                        norm.append(n['name'] + default)
                    d['normalizations'] = norm
        return cc
