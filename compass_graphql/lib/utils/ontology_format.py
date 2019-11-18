import json
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, XSD, RDFS, OWL

class OntologyFormat(object):

    class Formatter():

        def format_object(self, json_node):
            return []

        def format_predicate(self, json_node):
            if str(RDF.uri) in str(json_node):
                return str(json_node).replace(str(RDF.uri), '')
            elif str(RDFS.uri) in str(json_node):
                return str(json_node).replace(str(RDFS.uri), '')
            elif str(OWL.uri) in str(json_node):
                return str(json_node).replace(str(OWL.uri), '')
            return json_node

    class NCITFormatter(Formatter):

        def format_object(self, json_node):
            return [('name', json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value'])]

        def format_predicate(self, json_node):
            return json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value']

    class EdamFormatter(Formatter):

        def format_object(self, json_node):
            return [('name', json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value'])]

        def format_predicate(self, json_node):
            return json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value']

    class UOFormatter(Formatter):

        def format_object(self, json_node):
            return [('name', json_node['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value'])]

        def format_predicate(self, json_node):
            return json_node['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value']

    class POFormatter(Formatter):

        def format_object(self, json_node):
            return [('name', json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value'])]

        def format_predicate(self, json_node):
            return json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value']

    class BAOFormatter(Formatter):

        def format_object(self, json_node):
            return [('name', json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value'])]

        def format_predicate(self, json_node):
            return json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value']

    class EFOFormatter(Formatter):

        def format_object(self, json_node):
            return [('name', json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value'])]

        def format_predicate(self, json_node):
            return json_node[0]['http://www.w3.org/2000/01/rdf-schema#label'][0]['@value']


    class GOFormatter(Formatter):

        def format_object(self, json_node):
            return [('name', json_node['name'])]

    mapping = {
        'Gene ontology': GOFormatter,
        'Edam': EdamFormatter,
        'Nci thesaurus': NCITFormatter,
        'Unit of measurement': UOFormatter,
        'Plant ontology': POFormatter,
        'Bioassay ontology': BAOFormatter,
        'Bao properties': BAOFormatter,
        'Experimental factor ontology': EFOFormatter
    }

    @staticmethod
    def get_formatter(ontology_name):
        _class = OntologyFormat.mapping.get(ontology_name, None)
        if _class:
            return _class()
        return OntologyFormat.Formatter()
