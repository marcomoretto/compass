import graphene
from graphene import ObjectType
from graphene.types.resolver import dict_resolver
from graphql_relay import from_global_id, to_global_id
from rdflib import Graph, Literal, BNode, Namespace, RDF, URIRef, XSD, RDFS, OWL
from rdflib.serializer import Serializer
from rdflib import Graph, plugin, Namespace

from command.lib.db.compendium.sample import Sample

from command.lib.db.compendium.sample_annotation import SampleAnnotation

from command.lib.db.compendium.bio_feature import BioFeature
from compass_graphql.lib.schema.sample import SampleType
from compass_graphql.lib.utils.compendium_config import CompendiumConfig

from command.lib.db.compendium.sample import Sample
from django.db.models import Q
from command.lib.db.compendium.normalization_experiment import NormalizationExperiment
from command.lib.db.compendium.normalization import Normalization

from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup

import json


class SparqlResultType(ObjectType):
    rdf_triples = graphene.List(of_type=graphene.List(of_type=graphene.String))

    def resolve_rdf_triples(self, info, **kwargs):
        return self


class Query(object):
    sparql = graphene.Field(SparqlResultType,
                            compendium=graphene.String(required=True),
                            query=graphene.String(required=True),
                            target=graphene.String(required=True),
                            version=graphene.String(required=False),
                            database=graphene.String(required=False),
                            normalization=graphene.String(required=False))

    def resolve_sparql(self, info, **kwargs):
        if kwargs['target'] != 'sample' and kwargs['target'] != 'biofeature':
            raise Exception('target allowed values are sample or biofeature')

        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        result = []

        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        smp_ids = set()
        for exp in NormalizationExperiment.objects.using(db['name']).filter(Q(use_experiment=True) &
                                                                            Q(normalization=normalization)):
            smp_ids.update(exp.experiment.sample_set.all().values_list('id', flat=True))

        g_path = db['sample_annotation_path'] if kwargs['target'] == 'sample' else db['biofeature_annotation_path']
        g = Graph('Sleepycat', identifier=kwargs['target'])
        g.open(g_path, create=False)
        valid_samples = Sample.objects.using(db['name']).filter(id__in=smp_ids)
        for x in g.query(kwargs['query']):
            triple = []
            for t in x:
                if type(t) == Literal and t.datatype == RDF.ID:
                    if kwargs['target'] == 'sample':
                        s = valid_samples.filter(id=str(t)).first()
                    else:
                        s = BioFeature.objects.using(db['name']).filter(id=str(t)).first()
                    if s and kwargs['target'] == 'sample':
                        triple.append(to_global_id('SampleType', s.id))
                    elif s and kwargs['target'] == 'biofeature':
                        triple.append(to_global_id('BioFeatureType', s.id))
                    else:
                        triple.append(None)
                else:
                    triple.append(t)
            if sum([bool(x) for x in triple]):
                result.append(triple)
        g.close()
        return result
