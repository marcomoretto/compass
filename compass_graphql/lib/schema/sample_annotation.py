import graphene
from command.lib.db.compendium.sample_annotation import SampleAnnotation
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from compass_graphql.lib.schema.annotation_value import AnnotationValueType


class SampleAnnotationType(DjangoObjectType):
    class Meta:

        model = SampleAnnotation
        filter_fields = {
            'sample__sample_name': ['exact', 'icontains', 'istartswith', 'in'],
            'annotation_value__ontology_node__ontology__name': ['exact', 'icontains', 'istartswith', 'in'],
            'annotation_value__ontology_node__id': ['exact', 'in'],
            'annotation_value__ontology_node__original_id': ['exact', 'icontains', 'istartswith', 'in'],
        }
        interfaces = (graphene.relay.Node,)
        exclude_fields = ('annotation_value',)

    annotation = graphene.Field(AnnotationValueType)

    def resolve_annotation(self, info):
        return self.annotation_value


class Query(object):
    sample_annotations = DjangoFilterConnectionField(SampleAnnotationType, compendium=graphene.String(required=True))

    def resolve_sample_annotations(self, info, **kwargs):
        return SampleAnnotation.objects.using(kwargs['compendium']).all()
