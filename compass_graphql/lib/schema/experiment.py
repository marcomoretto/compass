import graphene
from command.lib.db.compendium.experiment import Experiment
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


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


class Query(object):
    experiments = DjangoFilterConnectionField(ExperimentType, compendium=graphene.String(required=True))

    def resolve_experiments(self, info, **kwargs):
        return Experiment.objects.using(kwargs['compendium']).all()
