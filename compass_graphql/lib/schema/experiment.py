import graphene
from command.lib.db.compendium.experiment import Experiment
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization
from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class ExperimentConnection(graphene.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()

    def resolve_total_count(root, info, **kwargs):
        return root.length


class ExperimentType(DjangoObjectType):
    class Meta:

        model = Experiment
        filter_fields = {
            'id': ['exact'],
            'experiment_access_id': ['exact', 'icontains', 'istartswith', 'in'],
            'experiment_name': ['exact', 'icontains'],
            'description': ['exact', 'icontains'],
            'comments': ['exact', 'icontains'],
            'data_source__source_name': ['exact'],
        }
        interfaces = (graphene.relay.Node,)
        connection_class = ExperimentConnection


class Query(object):
    experiments = DjangoFilterConnectionField(ExperimentType, compendium=graphene.String(required=True),
                                              version=graphene.String(required=False),
                                              database=graphene.String(required=False),
                                              normalization=graphene.String(required=False))

    def resolve_experiments(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        exp_ids = NormalizationExperiment.objects.using(db['name']).filter(
            Q(use_experiment=True) &
            Q(normalization=normalization)
        ).values_list('experiment_id', flat=True)
        return Experiment.objects.using(db['name']).filter(id__in=exp_ids)
