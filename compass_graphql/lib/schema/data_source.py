import graphene
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from command.lib.db.compendium.data_source import DataSource


class DataSourceType(DjangoObjectType):
    class Meta:

        model = DataSource
        filter_fields = {
            'id': ['exact'],
            'source_name': ['exact', 'icontains', 'istartswith', 'in'],
            'is_local': ['exact'],
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    data_sources = DjangoFilterConnectionField(DataSourceType, compendium=graphene.String(required=True))

    def resolve_data_sources(self, info, **kwargs):
        return DataSource.objects.using(kwargs['compendium']).all()
