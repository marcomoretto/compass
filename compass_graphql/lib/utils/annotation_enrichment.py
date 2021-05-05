from statsmodels.stats.multitest import multipletests
from command.lib.db.compendium.ontology_node import OntologyNode
from command.lib.db.compendium.bio_feature import BioFeature
from rdflib import Graph
import json
from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup
from scipy.stats import hypergeom
from command.lib.db.compendium.sample import Sample


class AnnotationEnrichment:

    def __init__(self, compendium_config, ontology_name, term_prefix=None):
        self.compendium_config = compendium_config
        self.ontology_name = ontology_name
        self.term_prefix = term_prefix
        self.nodes = dict(OntologyNode.objects.using(compendium_config['name']).filter(ontology__name=ontology_name).values_list('original_id', 'term_short_name'))

    def get_enrichment(self, items, p_value):
        raise NotImplementedError('Not implemented')

    def get_biofeature_annotations(self):
        annot = {}
        reverse_annot = {}
        g_path = self.compendium_config['biofeature_annotation_path']
        g = Graph('Sleepycat', identifier='biofeature')
        g.open(g_path, create=False)
        query = "SELECT ?s ?p ?o WHERE { ?s <http://purl.obolibrary.org/obo/NCIT_C44272> ?o FILTER (strstarts(str(?o), '" + self.term_prefix[0] + "')) }"
        for _s, _p, _o in g.query(query):
            s = str(_s)
            o = _o.replace(*self.term_prefix[:2])
            if o not in annot:
                annot[o] = set()
            if s not in reverse_annot:
                reverse_annot[s] = set()
            annot[o].add(s)
            reverse_annot[s].add(o)
        g.close()
        return annot, reverse_annot

    def get_sample_annotations(self):
        annot = {}
        reverse_annot = {}
        g_path = self.compendium_config['sample_annotation_path']
        g = Graph('Sleepycat', identifier='sample')
        g.open(g_path, create=False)
        query = "SELECT ?s ?p ?o WHERE { ?s <http://www.w3.org/1999/02/22-rdf-syntax-ns#type> ?o FILTER (strstarts(str(?o), '" + \
                self.term_prefix[0] + "')) }"
        for _s, _p, _o in g.query(query):
            s = str(_s)
            o = _o.replace(*self.term_prefix[:2])
            if o not in annot:
                annot[o] = set()
            if s not in reverse_annot:
                reverse_annot[s] = set()
            annot[o].add(s)
            reverse_annot[s].add(o)
        g.close()
        return annot, reverse_annot

    def samples_annotation_graph(self):
        _ss = NormalizationDesignGroup.objects.using(self.compendium_config['name']).all()
        g = Graph()
        for ss in _ss:
            for sample in ss.normalizationdesignsample_set.all():
                for ann in sample.sample.sampleannotation_set.all():
                    g.parse(data=json.dumps(ann.annotation), format='json-ld')
        return g


class BioFeatureAnnotationEnrichment(AnnotationEnrichment):

    def get_enrichment(self, items, p_value=0.05):
        annot, reverse_annot = self.get_biofeature_annotations()
        k = sum([str(bf) in reverse_annot for bf in items])  ## BF with at least one annotation
        N = len(reverse_annot)  ## Total number of bf with some annotation
        p_values = {}
        if k:
            for ont_term, bfs in annot.items():
                m = len(bfs)  ## Total BF associated to this ont_term
                x = sum([ont_term in reverse_annot.get(str(i), []) for i in items])  ## BF of the group of interest that are associated to this ont_term
                p_values[ont_term] = hypergeom(M=N, n=m, N=k).sf(x - 1)

            reject, corr_p_values, alphacSidak, alphacBonf = multipletests(list(p_values.values()), alpha=p_value, method="fdr_bh")
            p_values = dict(zip(p_values.keys(), corr_p_values))
        _p_values = {}
        for k, v in p_values.items():
            if v <= p_value:
                _p_values[k] = (self.nodes.get(k.replace(*self.term_prefix[-2:]), ''), v)
        return _p_values


class SampleAnnotationEnrichment(AnnotationEnrichment):

    def get_enrichment(self, items, p_value=0.05):
        annot, reverse_annot = self.get_sample_annotations()
        k = sum([str(ss) in reverse_annot for ss in items])  ## SS with at least one annotation
        N = len(reverse_annot)  ## Total number of ss with some annotation
        p_values = {}
        if k:
            for ont_term, sss in annot.items():
                m = len(sss)  ## Total SS associated to this ont_term
                x = sum([ont_term in reverse_annot.get(str(i), []) for i in items])  ## SS of the group of interest that are associated to this ont_term
                p_values[ont_term] = hypergeom(M=N, n=m, N=k).sf(x - 1)

            reject, corr_p_values, alphacSidak, alphacBonf = multipletests(list(p_values.values()), alpha=p_value, method="fdr_bh")
            p_values = dict(zip(p_values.keys(), corr_p_values))
        _p_values = {}
        for k, v in p_values.items():
            if v <= p_value:
                _p_values[k] = (self.nodes.get(k.replace(*self.term_prefix[-2:]), ''), v)
        return _p_values