import importlib
from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.io
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.conf import settings
from graphene import ObjectType
import graphene
from graphql_relay import from_global_id
import json
import plotly.graph_objs as go
import networkx as nx
from rdflib import Graph, plugin, Namespace
from rdflib.serializer import Serializer
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, XSD
from command.lib.db.compendium.ontology import Ontology
from command.lib.db.compendium.ontology_edge import OntologyEdge
from command.lib.db.compendium.ontology_node import OntologyNode

from compass_graphql.lib.utils.ontology_format import OntologyFormat
from compass_graphql.lib.utils.compendium_config import CompendiumConfig
import uuid


class AnnotationPrettyPrintType(ObjectType):
    rdf_triples = graphene.List(of_type=graphene.List(of_type=graphene.String))
    html = graphene.String()

    def resolve_rdf_triples(self, info, **kwargs):
        return self

    def resolve_html(self, info, **kwargs):
        nodes = set()
        edges = []
        for i, t in enumerate(self):
            nodes.add(t[0])
            nodes.add(t[2])
            edges.append("{{ data: {{ id: '{id}', source: '{source}', target: '{target}', label: '{label}' }} }}".format(
                id=i, label=t[1], source=t[0], target=t[2])
            )
        nodes = ["{{ data: {{ id: '{id}' }} }}".format(id=n) for n in list(nodes)]
        div_id = 'cy' + str(uuid.uuid4())
        cyjs = '<script>{src}</script>'.format(src=open(settings.BASE_DIR + static('compass/js/cytoscape/cytoscape.min.js'), 'r').read())
        style = '''
            <style>
                #{cy} {{
                    width: 100%;
                    height: 50%
                    top: 0px;
                    left: 0px;
                }}
            </style>
        '''.format(cy=div_id)
        div = '''
            <div id='{id}' style='border:1px solid gray; height: 500px;'></div>
        '''.format(id=div_id)
        js = '''
            <script>
              var cy = cytoscape({{
                container: document.getElementById('{cy}'),
                elements: [
                    {nodes},
                    {edges}  
                ],
                layout: {{
                    'name': 'breadthfirst'
                }},
                style: [
                {{
                    selector: 'node',
                    style: {{
                        shape: 'hexagon',
                        'background-color': 'red',
                        label: 'data(id)'
                    }}
                }},
                {{
                  selector: 'edge',
                  style: {{
                    'label': 'data(label)'
                  }}
                }}]
              }});
        </script>
        '''.format(cy=div_id, nodes=','.join(nodes), edges=','.join(edges))
        div = cyjs + style + div + js
        return div


class Query(object):
    annotation_pretty_print = graphene.Field(AnnotationPrettyPrintType,
                                             compendium=graphene.String(required=True),
                                             ids=graphene.List(required=True, of_type=graphene.ID)
                                             )

    def resolve_annotation_pretty_print(self, info, compendium, ids, **kwargs):
        triples = []
        for aid in ids:
            _class, _id = from_global_id(aid)
            if _class == 'BioFeatureType':
                _module = importlib.import_module('command.lib.db.compendium.bio_feature')
                _bf_class = getattr(_module, 'BioFeature')
                for ann in _bf_class.objects.using(compendium).get(id=_id).biofeatureannotation_set.all():
                    g = Graph().parse(data=json.dumps(ann.annotation), format='json-ld')
                    for s, p, o in g:
                        predicate = (str(p).split('/') or None)[-1]
                        obj = (str(o).split('/') or None)[-1]
                        node = OntologyNode.objects.using(compendium).filter(original_id=predicate).first()
                        if node:
                            predicate = OntologyFormat.get_formatter(node.ontology.name).format_predicate(node.json)
                        node = OntologyNode.objects.using(compendium).filter(original_id=obj).first()
                        if node:
                            for k, v in OntologyFormat.get_formatter(node.ontology.name).format_object(node.json):
                                triples.append(
                                    (obj, k, v)
                                )
                        triples.append(
                            (ann.bio_feature.name, predicate, obj)
                        )
            elif _class == 'SampleType':
                _module = importlib.import_module('command.lib.db.compendium.sample')
                _bf_class = getattr(_module, 'Sample')
                for ann in _bf_class.objects.using(compendium).get(id=_id).sampleannotation_set.all():
                    g = Graph().parse(data=json.dumps(ann.annotation), format='json-ld')
                    for s, p, o in g:
                        subject = ann.sample.sample_name
                        predicate = (str(p).split('/') or None)[-1]
                        predicate = (str(predicate).split('#') or None)[-1]
                        obj = (str(o).split('/') or None)[-1]
                        obj = (str(obj).split('#') or None)[-1]
                        if type(s) == BNode:
                            subject = s
                        node = OntologyNode.objects.using(compendium).filter(original_id=predicate).first()
                        if node and 'rdf-syntax' not in p:
                            predicate = OntologyFormat.get_formatter(node.ontology.name).format_predicate(node.json)
                        else:
                            predicate = OntologyFormat.Formatter().format_predicate(p)
                        node = OntologyNode.objects.using(compendium).filter(original_id=obj).first()
                        if node:
                            for k, v in OntologyFormat.get_formatter(node.ontology.name).format_object(node.json):
                                triples.append(
                                    (obj, k, v)
                                )
                        triples.append(
                            (subject, predicate, obj)
                        )


        return triples