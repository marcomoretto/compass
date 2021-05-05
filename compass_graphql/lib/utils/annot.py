from command.lib.db.compendium.sample import Sample
from rdflib import Graph
import json

from command.lib.db.compendium.ontology_node import OntologyNode
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, XSD

class Description:

    DEFAULT_CATEGORIES = ["NCIT_C16631", "PO_0007033", "type", "AGRO_00000322"]

    BIOFEATURE_ENRICHMENT_CATEGORIES = {
        'Gene ontology': ('GO_', 'GO_', 'GO_')
    }

    SAMPLESET_ENRICHMENT_CATEGORIES = {
        'Plant ontology': ('http://purl.obolibrary.org/obo/PO_', 'PO_', 'PO_')
    }

    __CONTRAST_SPARQL_QUERIES__ = [
        ('SELECT ?s ?p ?o WHERE { ?s <http://purl.obolibrary.org/obo/NCIT_C16631> ?o }', 'http://purl.obolibrary.org/obo/', ''), # genotype
        ('SELECT ?s ?p ?o WHERE { ?s <http://www.ebi.ac.uk/efo/EFO_0005136> ?o }', '', ''), # cultivar
        ('SELECT ?s ?p ?o WHERE { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o }', 'http://purl.obolibrary.org/obo/', ''), # type
        ('SELECT ?s ?p ?o WHERE { ?s <http://purl.obolibrary.org/obo/PO_0007033> ?o }', 'https://www.awri.com.au/wp-content/uploads/grapegrowth.pdf#', 'EL'), # dev stage
        ('SELECT ?s ?p1 ?o1 WHERE { ?s <http://purl.obolibrary.org/obo/AGRO_00000322> ?bn  . ?bn ?p1 ?o1}', 'http://purl.obolibrary.org/obo/', '')
    ]

    def __init__(self):
        pass

    @staticmethod
    def __format_terms__(terms, ont_map={}, case=str.lower):
        s = []
        for _t in terms:
            t = ont_map.get(_t, _t)
            s.append(
                '_'.join([case(w)[:5] if len(t.split(' ')) > 1 else case(w) for w in t.split(' ')])
            )

        return '|'.join(s)

    @staticmethod
    def get_sampleset_short_annotation_description(compendium_config, sampleset):
        if sampleset.normalization_experiment.normalization.name == 'limma' or sampleset.normalization_experiment.normalization.name == 'legacy':
            ref = sampleset.design['elements']['edges'][0]['data']['source']
            test= sampleset.design['elements']['edges'][0]['data']['target']
            ref_samples = []
            test_samples = []
            for node in sampleset.design['elements']['nodes']:
                if node['data']['type'] == 'sample' and node['data']['parent'] == ref:
                    ref_samples.append(node['data']['id'])
                elif node['data']['type'] == 'sample' and node['data']['parent'] == test:
                    test_samples.append(node['data']['id'])
            # reference graph
            ref_annot_graph = Graph()
            for sample in Sample.objects.using(compendium_config['name']).filter(id__in=ref_samples):
                for ann in sample.sampleannotation_set.all():
                    ref_annot_graph.parse(data=json.dumps(ann.annotation), format='json-ld')
            # test graph
            test_annot_graph = Graph()
            for sample in Sample.objects.using(compendium_config['name']).filter(id__in=test_samples):
                for ann in sample.sampleannotation_set.all():
                    test_annot_graph.parse(data=json.dumps(ann.annotation), format='json-ld')

            common_annot = list()
            different_annot = list()
            ont_map = {}
            for query, prefix, new_prefix in Description.__CONTRAST_SPARQL_QUERIES__:
                ref_annot = set()
                test_annot = set()
                for s, p, o in ref_annot_graph.query(query):
                    if type(o) == BNode:
                        continue
                    ref_annot.add(str(o.replace(prefix, new_prefix)))
                for s, p, o in test_annot_graph.query(query):
                    if type(o) == BNode:
                        continue
                    test_annot.add(str(o.replace(prefix, new_prefix)))

                ont_map.update(dict(OntologyNode.objects.using(compendium_config['name']).filter(
                    original_id__in=set.union(ref_annot, test_annot)).values_list('original_id', 'term_short_name')))

                if ref_annot - test_annot:
                    different_annot.extend(list(ref_annot) + list(test_annot))
                else:
                    common_annot.extend(list(ref_annot))

            desc_string = Description.__format_terms__(common_annot, ont_map) + '||' + Description.__format_terms__(different_annot, ont_map, case=str.upper)
        return desc_string