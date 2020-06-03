import graphene
from command.lib.db.compendium.platform_type import PlatformType
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


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
    platform_types = DjangoFilterConnectionField(PlatformTypeType, compendium=graphene.String(required=True),
                                                version=graphene.String(required=False),
                                                database=graphene.String(required=False),
                                                normalization=graphene.String(required=False))

    def resolve_platform_types(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        plt_ids = set()
        all_ids = set(PlatformType.objects.using(db['name']).values_list('id', flat=True))
        for exp in NormalizationExperiment.objects.using(db['name']).filter(Q(use_experiment=True) &
                                                                            Q(normalization=normalization)):
            for s in exp.experiment.sample_set.all():
                plt_ids.add(s.platform.platform_type_id)
                plt_ids.add(s.reporter_platform.platform_type_id)
                break
            if plt_ids == all_ids:
                break
        return PlatformType.objects.using(db['name']).filter(id__in=plt_ids)

