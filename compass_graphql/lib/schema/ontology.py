import graphene
from command.lib.db.compendium.ontology import Ontology
from command.lib.db.compendium.ontology_edge import OntologyEdge
from command.lib.db.compendium.ontology_node import OntologyNode
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
import networkx


class OntologyType(DjangoObjectType):
    class Meta:

        model = Ontology
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith', 'in'],
        }
        interfaces = (graphene.relay.Node,)

    structure = graphene.JSONString()

    def resolve_structure(self, info):
        compendium = self._state.db
        g = networkx.DiGraph()
        g.add_nodes_from(list(
            OntologyNode.objects.using(compendium).filter(ontology=self).values_list('original_id', 'json'))
        )
        g.add_edges_from(list(
            OntologyEdge.objects.using(compendium).filter(ontology=self).values_list(
                'source__original_id', 'target__original_id'))
        )
        return networkx.node_link_data(g)


class Query(object):
    ontology = DjangoFilterConnectionField(OntologyType, compendium=graphene.String(required=True))

    def resolve_ontology(self, info, **kwargs):
        return Ontology.objects.using(kwargs['compendium']).all()
