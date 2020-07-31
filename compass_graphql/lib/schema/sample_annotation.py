import graphene
from command.lib.db.compendium.sample_annotation import SampleAnnotation
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization

from command.lib.db.compendium.sample import Sample
from compass_graphql.lib.utils.compendium_config import CompendiumConfig

import operator
from django.db.models import Q
from functools import reduce
from command.lib.db.compendium.ontology_node import OntologyNode


class SampleAnnotationType(DjangoObjectType):
    class Meta:

        model = SampleAnnotation
        filter_fields = {
            'sample_id': ['exact', 'in'],
            'sample__sample_name': ['exact', 'icontains', 'istartswith', 'in']
        }
        interfaces = (graphene.relay.Node,)
        exclude_fields = ('annotation_value',)


class Query(object):
    sample_annotations = DjangoFilterConnectionField(SampleAnnotationType,
                                                     compendium=graphene.String(required=True),
                                                     version=graphene.String(required=False),
                                                     database=graphene.String(required=False),
                                                     normalization=graphene.String(required=False),
                                                     ontology_id=graphene.String(),
                                                     annotation_term=graphene.String())

    def resolve_sample_annotations(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        smp_ids = set()
        for exp in NormalizationExperiment.objects.using(db['name']).filter(Q(use_experiment=True) &
                                                                            Q(normalization=normalization)):
            smp_ids.update(exp.experiment.sample_set.all().values_list('id', flat=True))
        rs = SampleAnnotation.objects.using(db['name']).filter(sample_id__in=smp_ids)
        if 'ontology_id' in kwargs:
            return rs.filter(annotation__icontains=kwargs['ontology_id'])
        if 'annotation_term' in kwargs:
            ooids = [o.original_id for o in OntologyNode.objects.using(db['name']).filter(term_short_name__icontains=kwargs['annotation_term'])]
            return rs.filter(reduce(operator.or_, (Q(annotation__icontains=x) for x in ooids)))
        return rs
