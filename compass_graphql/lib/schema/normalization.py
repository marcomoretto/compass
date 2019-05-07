import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from command.lib.db.compendium.normalization import Normalization


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
        return Normalization.objects.using(kwargs['compendium']).all()
