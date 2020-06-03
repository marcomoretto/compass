import graphene
from command.lib.db.compendium.bio_feature_annotation import BioFeatureAnnotation
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

from compass_graphql.lib.utils.compendium_config import CompendiumConfig


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
                                                         normalization=graphene.String(required=False))

    def resolve_biofeature_annotations(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        return BioFeatureAnnotation.objects.using(db['name']).all()

