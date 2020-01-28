import graphene
from command.lib.db.compendium.sample import Sample
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_relay import from_global_id

from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup


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
    samples = DjangoFilterConnectionField(SampleType,
                                          compendium=graphene.String(required=True),
                                          sample_set=graphene.ID(required=False),
                                          annotation_ontology_id=graphene.String(required=False))

    def resolve_samples(self, info, sample_set=None, annotation_ontology_id=None, **kwargs):
        qs = None
        if sample_set:
            ss_id = from_global_id(sample_set)[1]
            qs = [s.sample for s in NormalizationDesignGroup.objects.using(kwargs['compendium']).get(id=ss_id).normalizationdesignsample_set.all()]
        if annotation_ontology_id:
            qs = [s for s in Sample.objects.using(kwargs['compendium']) if s.sampleannotation_set.filter(
                annotation__icontains=annotation_ontology_id).count() > 0]
        if qs:
            return qs
        return Sample.objects.using(kwargs['compendium']).all()
