import graphene
from command.lib.db.compendium.ontology import Ontology
from command.lib.db.compendium.ontology_edge import OntologyEdge
from command.lib.db.compendium.ontology_node import OntologyNode
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
import networkx

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


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
            OntologyNode.objects.using(compendium).filter(ontology=self).values_list('original_id'))
        )
        g.add_edges_from(list(
            OntologyEdge.objects.using(compendium).filter(ontology=self).values_list(
                'source__original_id', 'target__original_id'))
        )
        return networkx.node_link_data(g)


class Query(object):
    ontology = DjangoFilterConnectionField(OntologyType, compendium=graphene.String(required=True),
                                           version=graphene.String(required=False),
                                           database=graphene.String(required=False),
                                           normalization=graphene.String(required=False))

    def resolve_ontology(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        return Ontology.objects.using(db['name']).all()
