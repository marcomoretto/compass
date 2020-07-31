import graphene
from command.lib.db.compendium.bio_feature_annotation import BioFeatureAnnotation
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from compass_graphql.lib.utils.compendium_config import CompendiumConfig

import operator
from django.db.models import Q
from functools import reduce
from command.lib.db.compendium.ontology_node import OntologyNode


class BioFeatureAnnotationType(DjangoObjectType):
    class Meta:

        model = BioFeatureAnnotation
        filter_fields = {
            'bio_feature__id': ['exact', 'in'],
            'bio_feature__name': ['exact', 'icontains', 'istartswith', 'in']
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    biofeature_annotations = DjangoFilterConnectionField(BioFeatureAnnotationType, compendium=graphene.String(required=True),
                                                         version=graphene.String(required=False),
                                                         database=graphene.String(required=False),
                                                         normalization=graphene.String(required=False),
                                                         ontology_id=graphene.String(),
                                                         annotation_term=graphene.String())

    def resolve_biofeature_annotations(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        rs = BioFeatureAnnotation.objects.using(db['name']).all()
        if 'ontology_id' in kwargs:
            return rs.filter(annotation__icontains=kwargs['ontology_id'])
        if 'annotation_term' in kwargs:
            ooids = [o.original_id for o in OntologyNode.objects.using(db['name']).filter(term_short_name__icontains=kwargs['annotation_term'])]
            return rs.filter(reduce(operator.or_, (Q(annotation__icontains=x) for x in ooids)))
        return rs

