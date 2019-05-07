import graphene
from command.lib.db.compendium.bio_feature import BioFeature
from command.lib.db.compendium.bio_feature_fields import BioFeatureFields
from command.lib.db.compendium.bio_feature_values import BioFeatureValues
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType
from graphql_relay import from_global_id

from compass_graphql.lib.schema.biofeature_annotation import BioFeatureAnnotationType


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
            'name': ['exact', 'icontains', 'istartswith', 'in'],
            'description': ['exact', 'icontains'],
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    biofeatures = DjangoFilterConnectionField(BioFeatureType, compendium=graphene.String(required=True), id__in=graphene.ID())
    biofeature_value = DjangoFilterConnectionField(BioFeatureValueType)
    biofeature_field = DjangoFilterConnectionField(BioFeatureFieldType)

    def resolve_biofeatures(self, info, **kwargs):
        rs =  BioFeature.objects.using(kwargs['compendium']).all()
        if 'id__in' in kwargs:
            rs = rs.filter(id__in=[from_global_id(i)[1] for i in kwargs['id__in'].split(',')])
        return rs

    def resolve_biofeature_field(self, info, **kwargs):
        return BioFeatureFields.objects.using(kwargs['compendium']).all()
