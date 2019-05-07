import graphene
from command.lib.db.compendium.platform_type import PlatformType
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class PlatformTypeType(DjangoObjectType):
    class Meta:

        model = PlatformType
        filter_fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains', 'istartswith', 'in'],
            'description': ['exact', 'icontains'],
            'bio_feature_reporter_name': ['exact'],
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    platform_types = DjangoFilterConnectionField(PlatformTypeType, compendium=graphene.String(required=True))

    def resolve_platform_types(self, info, **kwargs):
        return PlatformType.objects.using(kwargs['compendium']).all()
