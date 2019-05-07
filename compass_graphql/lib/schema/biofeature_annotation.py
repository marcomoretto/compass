import graphene
from command.lib.db.compendium.annotation_value import AnnotationValue
from command.lib.db.compendium.bio_feature_annotation import BioFeatureAnnotation
from command.lib.db.compendium.ontology import Ontology
from command.lib.db.compendium.ontology_node import OntologyNode
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class BioFeatureAnnotationType(DjangoObjectType):
    class Meta:

        model = BioFeatureAnnotation
        filter_fields = {
            'bio_feature__name': ['exact', 'icontains', 'istartswith', 'in'],
            'annotation_value__ontology_node__ontology__name': ['exact', 'icontains', 'istartswith', 'in'],
            'annotation_value__ontology_node__id': ['exact', 'in'],
            'annotation_value__ontology_node__original_id': ['exact', 'icontains', 'istartswith', 'in'],
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    biofeature_annotations = DjangoFilterConnectionField(BioFeatureAnnotationType, compendium=graphene.String(required=True))

    def resolve_biofeature_annotations(self, info, **kwargs):
        return BioFeatureAnnotation.objects.using(kwargs['compendium']).all()
