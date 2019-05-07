import graphene
from command.lib.db.compendium.platform import Platform
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class PlatformType(DjangoObjectType):
    class Meta:

        model = Platform
        filter_fields = {
            'id': ['exact'],
            'platform_access_id': ['exact', 'icontains', 'istartswith', 'in'],
            'platform_name': ['exact', 'icontains'],
            'description': ['exact', 'icontains'],
            'platform_type__name': ['exact'],
            'data_source__source_name': ['exact'],
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    platforms = DjangoFilterConnectionField(PlatformType, compendium=graphene.String(required=True))

    def resolve_platforms(self, info, **kwargs):
        return Platform.objects.using(kwargs['compendium']).all()
