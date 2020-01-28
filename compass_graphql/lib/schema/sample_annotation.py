import graphene
from command.lib.db.compendium.sample_annotation import SampleAnnotation
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


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
                                                     ontology_id=graphene.String())

    def resolve_sample_annotations(self, info, **kwargs):
        if 'ontology_id' in kwargs:
            return SampleAnnotation.objects.using((kwargs['compendium'])).filter(annotation__icontains=kwargs['ontology_id'])
        return SampleAnnotation.objects.using(kwargs['compendium']).all()

