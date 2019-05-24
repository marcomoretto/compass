import graphene
from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup
from command.lib.db.compendium.normalization_design_sample import NormalizationDesignSample
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_relay.node.node import to_global_id
from graphql_relay.node.node import from_global_id

from compass_graphql.lib.schema.sample import SampleType


class SampleSetSampleType(DjangoObjectType):
    class Meta:

        model = NormalizationDesignSample
        filter_fields = {
            'id': ['exact']
        }
        interfaces = (graphene.relay.Node,)


class SampleSetType(DjangoObjectType):
    class Meta:

        model = NormalizationDesignGroup
        filter_fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains', 'istartswith', 'in'],

        }
        interfaces = (graphene.relay.Node,)

    normalization = graphene.String()

    def resolve_normalization(self, info, **kwargs):
        return self.normalization_experiment.normalization.name


class Query(object):
    sample_sets = DjangoFilterConnectionField(SampleSetType,
                                              compendium=graphene.String(required=True),
                                              normalization=graphene.String(),
                                              samples=graphene.List(of_type=graphene.ID),
                                              id__in=graphene.ID())

    def resolve_sample_sets(self, info, **kwargs):
        rs = NormalizationDesignGroup.objects.using(kwargs['compendium'])
        if 'normalization' in kwargs:
            rs = rs.filter(normalization_experiment__normalization__name=kwargs['normalization'])
        if 'samples' in kwargs:
            nds_ids = [from_global_id(sid)[1] for sid in kwargs['samples']]
            ndg_ids = NormalizationDesignSample.objects.using(kwargs['compendium']).filter(sample_id__in=nds_ids).\
                values_list('normalization_design_id', flat=True)
            rs = rs.filter(id__in=ndg_ids)
        if 'id__in' in kwargs:
            rs = rs.filter(id__in=[from_global_id(i)[1] for i in kwargs['id__in'].split(',')])
        return rs
