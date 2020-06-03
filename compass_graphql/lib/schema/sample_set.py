import re

import graphene
from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup
from command.lib.db.compendium.normalization_design_sample import NormalizationDesignSample
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_relay.node.node import to_global_id
from graphql_relay.node.node import from_global_id
from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization

from command.lib.db.compendium.normalized_data import NormalizedData
from compass_graphql.lib.schema.sample import SampleType
from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class SampleSetConnection(graphene.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()

    def resolve_total_count(root, info, **kwargs):
        return root.length


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
        connection_class = SampleSetConnection

    normalization = graphene.String()

    def resolve_normalization(self, info, **kwargs):
        return self.normalization_experiment.normalization.name


class Query(object):
    sample_sets = DjangoFilterConnectionField(SampleSetType,
                                              compendium=graphene.String(required=True),
                                              version=graphene.String(required=False),
                                              database=graphene.String(required=False),
                                              normalization=graphene.String(),
                                              samples=graphene.List(of_type=graphene.ID),
                                              experiments=graphene.List(of_type=graphene.ID),
                                              id__in=graphene.ID())

    def resolve_sample_sets(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        smp_set_ids = set()
        for exp in NormalizationExperiment.objects.using(db['name']).filter(Q(use_experiment=True) &
                                                                            Q(normalization=normalization)):
            smp_set_ids.update(exp.normalizationdesigngroup_set.all().values_list('id', flat=True))
        rs = NormalizationDesignGroup.objects.using(db['name']).filter(id__in=smp_set_ids)
        if 'samples' in kwargs:
            nds_ids = [from_global_id(sid)[1] for sid in kwargs['samples']]
            ndg_ids = NormalizationDesignSample.objects.using(db['name']).filter(sample_id__in=nds_ids).\
                values_list('normalization_design_id', flat=True)
            rs = rs.filter(id__in=ndg_ids)
        if 'experiments' in kwargs:
            e_ids = [from_global_id(eid)[1] for eid in kwargs['experiments']]
            ngd_ids = NormalizationDesignGroup.objects.using(db['name']).filter(
                normalization_experiment__experiment_id__in=e_ids
            ).values_list('id', flat=True)
            rs = rs.filter(id__in=ngd_ids)
        if 'id__in' in kwargs:
            rs = rs.filter(id__in=[from_global_id(i)[1] for i in kwargs['id__in'].split(',')])
        return rs
