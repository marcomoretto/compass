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

        g_path = db['sample_annotation_path'] if kwargs['target'] == 'sample' else db['biofeature_annotation_path']
        g = Graph('Sleepycat', identifier=kwargs['target'])
        g.open(g_path, create=False)
        for x in g.query(kwargs['query']):
            triple = []
            for t in x:
                if type(t) == Literal and t.datatype == RDF.ID:
                    if kwargs['target'] == 'sample':
                        s = Sample.objects.using(db['name']).filter(id=str(t)).first()
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
            result.append(triple)
        g.close()
        return result
