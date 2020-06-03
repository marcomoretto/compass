import graphene
from command.lib.db.compendium.ontology_node import OntologyNode
from graphene.types.generic import GenericScalar
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


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
    ontology_node = DjangoFilterConnectionField(OntologyNodeType, compendium=graphene.String(required=True),
                                                version=graphene.String(required=False),
                                                database=graphene.String(required=False),
                                                normalization=graphene.String(required=False))

    def resolve_ontology_node(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        return OntologyNode.objects.using(db['name']).all()
