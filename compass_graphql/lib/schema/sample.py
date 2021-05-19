import graphene
from command.lib.db.compendium.sample import Sample
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_relay import from_global_id
from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization

from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class SampleConnection(graphene.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()

    def resolve_total_count(root, info, **kwargs):
        return root.length


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
        connection_class = SampleConnection


class Query(object):
    samples = DjangoFilterConnectionField(SampleType,
                                          compendium=graphene.String(required=True),
                                          version=graphene.String(required=False),
                                          database=graphene.String(required=False),
                                          normalization=graphene.String(required=False),
                                          sample_set=graphene.ID(required=False),
                                          annotation_ontology_id=graphene.String(required=False),
                                          id__in=graphene.ID())

    def resolve_samples(self, info, sample_set=None, annotation_ontology_id=None, **kwargs):
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
        qs = Sample.objects.using(db['name']).filter(id__in=smp_ids)
        if 'id__in' in kwargs:
            valid_ids = []
            for i in kwargs['id__in'].split(','):
                try:
                    valid_ids.append(from_global_id(i)[1])
                except Exception as e:
                    pass
            qs = qs.filter(id__in=valid_ids)
        if sample_set:
            ss_id = from_global_id(sample_set)[1]
            qs = [s.sample for s in NormalizationDesignGroup.objects.using(db['name']).get(id=ss_id).normalizationdesignsample_set.all()]
        if annotation_ontology_id:
            qs = [s for s in Sample.objects.using(kwargs['compendium']) if s.sampleannotation_set.filter(
                annotation__icontains=annotation_ontology_id).count() > 0]
        return qs
