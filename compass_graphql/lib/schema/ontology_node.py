import json

import graphene
from command.lib.db.compendium.ontology_node import OntologyNode
from graphene.types.generic import GenericScalar
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_relay import from_global_id

from command.lib.db.compendium.ontology_edge import OntologyEdge

from command.lib.db.compendium.sample import Sample
from rdflib import Graph

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class OntologyNodeType(DjangoObjectType):
    json = GenericScalar()

    class Meta:

        model = OntologyNode
        filter_fields = {
            'id': ['exact'],
            'original_id': ['exact', 'icontains', 'istartswith', 'in'],
            'ontology__name': ['exact', 'icontains', 'in']
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    ontology_node = DjangoFilterConnectionField(OntologyNodeType, compendium=graphene.String(required=True),
                                                version=graphene.String(required=False),
                                                database=graphene.String(required=False),
                                                normalization=graphene.String(required=False),
                                                used_in_samples=graphene.List(graphene.ID),
                                                used_in_biofeatures=graphene.List(graphene.ID),
                                                ancestor_of=graphene.ID(),
                                                descendant_of=graphene.ID())

    def resolve_ontology_node(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        rs = OntologyNode.objects.using(db['name']).all()
        if 'used_in_samples' in kwargs:
            sids = [from_global_id(i)[1] for i in kwargs['used_in_samples']]
            samples = Sample.objects.using(db['name']).filter(id__in=sids)
            g = Graph()
            for sample in samples:
                for ann in sample.sampleannotation_set.all():
                    g.parse(data=json.dumps(ann.annotation), format='json-ld')
            oids = set()
            for s, p, o in g:
                oids.add(p.split('/')[-1].split('#')[-1])
                oids.add(o.split('/')[-1].split('#')[-1])
            return rs.filter(original_id__in=oids)
        if 'ancestor_of' in kwargs:
            ancestors = []
            nid = from_global_id(kwargs['ancestor_of'])[1]
            start_node = OntologyNode.objects.using(db['name']).get(id=nid)
            nodes =[start_node]
            while True:
                anc_edges = OntologyEdge.objects.using(db['name']).filter(target__in=nodes)
                nodes[:] = []
                for edge in anc_edges:
                    ancestors.append(edge.source)
                    nodes.append(edge.source.id)
                if not nodes:
                    break
            return rs.filter(id__in=[a.id for a in ancestors])
        if 'descendant_of' in kwargs:
            descendant = []
            nid = from_global_id(kwargs['descendant_of'])[1]
            start_node = OntologyNode.objects.using(db['name']).get(id=nid)
            nodes =[start_node]
            while True:
                des_edges = OntologyEdge.objects.using(db['name']).filter(source__in=nodes)
                nodes[:] = []
                for edge in des_edges:
                    descendant.append(edge.target)
                    nodes.append(edge.target.id)
                if not nodes:
                    break
            return rs.filter(id__in=[a.id for a in descendant])

        return rs
