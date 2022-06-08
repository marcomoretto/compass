import importlib

import graphene
from graphene import ObjectType
from graphene.types.resolver import dict_resolver
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required
from graphql_relay import from_global_id

from command.lib.db.compendium.sample import Sample

from command.lib.db.compendium.ontology_node import OntologyNode
from compass_graphql.lib.schema.bio_feature import BioFeatureType
from compass_graphql.lib.schema.sample import SampleType
from compass_graphql.lib.schema.sample_set import SampleSetType
from compass_graphql.lib.utils.compendium_config import CompendiumConfig
from compass_graphql.lib.utils.module import InitModuleProxy, get_normalization_name_from_sample_set_id


class SampleDescriptionSummaryCategory(ObjectType):
    class Meta:
        default_resolver = dict_resolver

    original_id = graphene.String()
    term_short_name = graphene.String()
    samples = graphene.List(of_type=SampleType)


class SampleDescriptionSummary(ObjectType):
    class Meta:
        default_resolver = dict_resolver

    category = graphene.String()
    details = graphene.List(SampleDescriptionSummaryCategory)


class AnnotationEnrichmentOntologyTerm(ObjectType):
    class Meta:
        default_resolver = dict_resolver

    ontology_id = graphene.String()
    description = graphene.String()
    p_value = graphene.Float()


class AnnotationEnrichment(ObjectType):
    class Meta:
        default_resolver = dict_resolver

    ontology = graphene.String()
    ontology_term = graphene.List(AnnotationEnrichmentOntologyTerm)

    def resolve_ontology(self, info, **kwargs):
        return self['ontology']

    def resolve_ontology_term(self, info, **kwargs):
        return self['ontology_term']


class ProxyModuleType(ObjectType):
    normalization = graphene.String()
    normalized_values = graphene.List(graphene.List(of_type=graphene.Float))
    biofeatures = DjangoFilterConnectionField(BioFeatureType, compendium=graphene.String())
    sample_sets = DjangoFilterConnectionField(SampleSetType,
                                              compendium=graphene.String(),
                                              samples=graphene.List(of_type=graphene.ID))
    samples_description_summary = graphene.List(SampleDescriptionSummary,
                                                categories=graphene.List(graphene.String))
    biofeature_annotation_enrichment = graphene.List(AnnotationEnrichment,
                                          corr_p_value_cutoff=graphene.Float())
    sampleset_annotation_enrichment = graphene.List(AnnotationEnrichment,
                                                     corr_p_value_cutoff=graphene.Float())

    def resolve_sampleset_annotation_enrichment(self, info, **kwargs):
        p_value = float(kwargs.get('corr_p_value_cutoff', 0.05))
        ann_enrichment = self.get_annotation_enrichment(category='sample', p_value=p_value)

        return [{
                'ontology': k,
                'ontology_term': [{
                    'ontology_id': x,
                    'description': y[0],
                    'p_value': y[1]
                } for x, y in v.items()]
            } for k, v in ann_enrichment.items()]

    def resolve_biofeature_annotation_enrichment(self, info, **kwargs):
        p_value = float(kwargs.get('corr_p_value_cutoff', 0.05))
        ann_enrichment = self.get_annotation_enrichment(category='biofeature', p_value=p_value)

        return [{
                'ontology': k,
                'ontology_term': [{
                    'ontology_id': x,
                    'description': y[0],
                    'p_value': y[1]
                } for x, y in v.items()]
            } for k, v in ann_enrichment.items()]

    def resolve_samples_description_summary(self, info, **kwargs):
        g = self.samples_annotation_graph()

        summary = []
        cc = CompendiumConfig()
        ann_desc_class = cc.get_annotation_description_class(self.db, self.normalization_name)
        _module = importlib.import_module('.'.join(ann_desc_class.split('.')[:-1]))
        _class = ann_desc_class.split('.')[-1]
        _ann_desc_class = getattr(_module, _class)

        categories = kwargs.get('categories', _ann_desc_class.DEFAULT_CATEGORIES)
        for _cat in categories:
            cat = {}

            query_cat = "SELECT ?s ?p ?o WHERE {?s ?p ?o FILTER(strends(str(?p), '" + _cat + "'))}"
            _abs = str(g.absolutize(''))
            for s, p, o in g.query(query_cat):
                _id = str(s).replace(_abs, '')
                _gt = str(o).split('/')[-1]
                if '#' in _gt:
                    _gt = _gt.split('#')[-1]
                if not _id.isnumeric():
                    continue
                if _gt not in cat:
                    cat[_gt] = set()
                cat[_gt].add(_id)

            _ont_map = dict(OntologyNode.objects.using(self.db['name']).filter(original_id__in=list(cat.keys())).values_list('original_id', 'term_short_name'))
            for k, v in cat.items():
                cat[k] = Sample.objects.using(self.db['name']).filter(id__in=v)
            summary.append(
                {'category': _cat,
                 'details': [{'original_id': k, 'term_short_name': _ont_map.get(k, k), 'samples': v} for k, v in cat.items()]}
            )

        return summary

    def resolve_normalization(self, info, **kwargs):
        return self.normalization

    def resolve_sample_sets(self, info, **kwargs):
        return self.get_sample_sets()

    def resolve_biofeatures(self, info, **kwargs):
        return self.get_biological_features()

    def resolve_normalized_values(self, info):
        return self.get_normalized_values()


class Query(object):
    modules = graphene.Field(ProxyModuleType,
                             compendium=graphene.String(required=True),
                             version=graphene.String(required=False),
                             database=graphene.String(required=False),
                             normalization=graphene.String(required=False),
                             rank=graphene.String(),
                             biofeatures_ids=graphene.List(of_type=graphene.ID),
                             sampleset_ids=graphene.List(of_type=graphene.ID))

    def resolve_modules(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        if "sampleset_ids" in kwargs:
            n = get_normalization_name_from_sample_set_id(db, from_global_id(kwargs['sampleset_ids'][0])[1])
            #db = cc.get_db_from_normalization(n)
        else:
            n = kwargs.get('normalization', db['default_normalization'])
        rank = kwargs['rank'] if 'rank' in kwargs else None
        plot_class = cc.get_plot_class(db, n)
        _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
        _class = plot_class.split('.')[-1]
        _plot_class = getattr(_module, _class)
        module_proxy_class = InitModuleProxy(_plot_class)

        m = module_proxy_class(db, info.context.user, n)
        if "biofeatures_ids" in kwargs:
            if len(set(kwargs["biofeatures_ids"])) < len(list(kwargs["biofeatures_ids"])):
                raise Exception('You have duplicated biofeature ids!')
            m.set_global_biofeatures(kwargs["biofeatures_ids"])
        if "sampleset_ids" in kwargs:
            if len(set(kwargs["sampleset_ids"])) < len(list(kwargs["sampleset_ids"])):
                raise Exception('You have duplicated sampleset ids!')
            m.set_global_samplesets(kwargs["sampleset_ids"])
        if len(m.biological_features) == 0:
            m.infer_biological_features(rank)
        if len(m.sample_sets) == 0:
            if n is None:
                raise Exception('If sample_sets is empty you need to provide a normalization for the automatic retrieval of sample_sets')
            m.infer_sample_sets(rank)
        return m
