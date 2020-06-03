import graphene
from command.lib.db.compendium.platform import Platform
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class PlatformConnection(graphene.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()

    def resolve_total_count(root, info, **kwargs):
        return root.length


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
        connection_class = PlatformConnection


class Query(object):
    platforms = DjangoFilterConnectionField(PlatformType, compendium=graphene.String(required=True),
                                              version=graphene.String(required=False),
                                              database=graphene.String(required=False),
                                              normalization=graphene.String(required=False))

    def resolve_platforms(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        plt_ids = set()
        for exp in NormalizationExperiment.objects.using(db['name']).filter(Q(use_experiment=True) &
                    Q(normalization=normalization)):
            for s in exp.experiment.sample_set.all():
                plt_ids.add(s.platform_id)
                plt_ids.add(s.reporter_platform_id)
        return Platform.objects.using(db['name']).filter(id__in=plt_ids)

