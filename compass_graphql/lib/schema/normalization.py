import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from command.lib.db.compendium.normalization import Normalization

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class NormalizationType(DjangoObjectType):
    class Meta:

        model = Normalization
        filter_fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains', 'istartswith', 'in'],
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    normalizations = DjangoFilterConnectionField(NormalizationType, compendium=graphene.String(required=True))

    def resolve_normalizations(self, info, **kwargs):
        conf = CompendiumConfig(kwargs['compendium'])
        return Normalization.objects.using(kwargs['compendium']).filter(name__in=conf.get_normalization_names())
