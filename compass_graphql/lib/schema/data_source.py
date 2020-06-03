import graphene
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from command.lib.db.compendium.data_source import DataSource
from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


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
    data_sources = DjangoFilterConnectionField(DataSourceType, compendium=graphene.String(required=True),
                                               version=graphene.String(required=False),
                                               database=graphene.String(required=False),
                                               normalization=graphene.String(required=False))

    def resolve_data_sources(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        ds_ids = set()
        for exp in NormalizationExperiment.objects.using(db['name']).filter(Q(use_experiment=True) &
                Q(normalization=normalization)):
            ds_ids.add(exp.experiment.data_source_id)
        return DataSource.objects.using(db['name']).filter(id__in=ds_ids)
