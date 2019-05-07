import graphene
from command.lib.db.compendium.sample import Sample
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class SampleType(DjangoObjectType):
    class Meta:

        model = Sample
        filter_fields = {
            'id': ['exact'],
            'sample_name': ['exact', 'icontains', 'istartswith', 'in'],
            'description': ['exact', 'icontains'],
            'experiment__experiment_access_id': ['exact', 'icontains'],
            'platform__platform_access_id': ['exact', 'icontains'],
            'reporter_platform__platform_access_id': ['exact', 'icontains'],
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    samples = DjangoFilterConnectionField(SampleType, compendium=graphene.String(required=True))

    def resolve_samples(self, info, **kwargs):
        return Sample.objects.using(kwargs['compendium']).all()
