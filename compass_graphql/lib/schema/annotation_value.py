import graphene
from command.lib.db.compendium.annotation_value import AnnotationValue
from command.lib.db.compendium.ontology import Ontology
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class AnnotationValueType(DjangoObjectType):
    class Meta:

        model = AnnotationValue
        filter_fields = []
        interfaces = (graphene.relay.Node,)


class Query(object):
    annotation = DjangoFilterConnectionField(AnnotationValueType, compendium=graphene.String(required=True))
    ontology_node_annotation_value = DjangoFilterConnectionField(AnnotationValueType, compendium=graphene.String(required=True))

    def resolve_annotation(self, info, **kwargs):
        return AnnotationValue.objects.using(kwargs['compendium']).all()
