import graphene
from command.lib.db.compendium.bio_feature import BioFeature
from command.lib.db.compendium.bio_feature_fields import BioFeatureFields
from command.lib.db.compendium.bio_feature_values import BioFeatureValues
from command.lib.db.compendium.normalized_data import NormalizedData
from django.db.models import Q
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_relay import from_global_id
import re
import operator
from django.db.models import Q
from functools import reduce

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class BioFeatureConnection(graphene.Connection):
    class Meta:
        abstract = True

    total_count = graphene.Int()

    def resolve_total_count(root, info, **kwargs):
        return root.length


class BioFeatureFieldType(DjangoObjectType):
    class Meta:
        model = BioFeatureFields
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith'],
        }
        interfaces = (graphene.relay.Node,)


class BioFeatureValueType(DjangoObjectType):
    class Meta:
        model = BioFeatureValues
        filter_fields = {
            'bio_feature_field__name': ['exact', 'icontains', 'istartswith'],
        }
        interfaces = (graphene.relay.Node,)


class BioFeatureType(DjangoObjectType):

    class Meta:

        model = BioFeature
        filter_fields = {
            'id': ['exact'],
            'name': ['exact', 'icontains', 'istartswith'],
            'description': ['exact', 'icontains'],
        }
        interfaces = (graphene.relay.Node,)
        connection_class = BioFeatureConnection


class Query(object):
    biofeatures = DjangoFilterConnectionField(BioFeatureType, compendium=graphene.String(required=True),
                                              version=graphene.String(required=False),
                                              database=graphene.String(required=False),
                                              normalization=graphene.String(required=False),
                                              id__in=graphene.ID(),
                                              name__in=graphene.String())


    def resolve_biofeatures(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        rs = BioFeature.objects.using(db['name']).all()
        if 'id__in' in kwargs:
            valid_ids = []
            for i in kwargs['id__in'].split(','):
                try:
                    valid_ids.append(from_global_id(i)[1])
                except Exception as e:
                    pass
            rs = rs.filter(id__in=valid_ids)
        if 'name__in' in kwargs:
            rs = rs.filter(reduce(operator.or_, (Q(name__icontains=x) for x in kwargs['name__in'].split(','))))
        return rs
