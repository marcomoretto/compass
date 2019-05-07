import graphene
from command.lib.db.compendium.ontology_node import OntologyNode
from graphene.types.generic import GenericScalar
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType


class OntologyNodeType(DjangoObjectType):
    json = GenericScalar()

    class Meta:

        model = OntologyNode
        filter_fields = {
            'original_id': ['exact', 'icontains', 'istartswith', 'in'],
            'ontology__name': ['exact', 'icontains', 'in']
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    ontology_node = DjangoFilterConnectionField(OntologyNodeType, compendium=graphene.String(required=True))

    def resolve_ontology_node(self, info, **kwargs):
        return OntologyNode.objects.using(kwargs['compendium']).all()
