import graphene
from django.db.models import Q
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
    normalizations = DjangoFilterConnectionField(NormalizationType, compendium=graphene.String(required=True),
                                                 version=graphene.String(required=False),
                                                 database=graphene.String(required=False),
                                                 normalization=graphene.String(required=False))

    def resolve_normalizations(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = [n['name'] for n in db['normalizations']]
        if 'normalization' in kwargs:
            n = [kwargs['normalization']]

        return Normalization.objects.using(db['name']).filter(Q(name__in=n) & Q(is_public=True))
