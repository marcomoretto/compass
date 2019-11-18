import graphene
from command.lib.db.compendium.bio_feature_annotation import BioFeatureAnnotation
from graphene_django.filter import DjangoFilterConnectionField
from graphene_django.types import DjangoObjectType

class BioFeatureAnnotationType(DjangoObjectType):
    class Meta:

        model = BioFeatureAnnotation
        filter_fields = {
            'bio_feature__id': ['exact', 'in'],
            'bio_feature__name': ['exact', 'icontains', 'istartswith', 'in']
        }
        interfaces = (graphene.relay.Node,)


class Query(object):
    biofeature_annotations = DjangoFilterConnectionField(BioFeatureAnnotationType, compendium=graphene.String(required=True))

    def resolve_biofeature_annotations(self, info, **kwargs):
        return BioFeatureAnnotation.objects.using(kwargs['compendium']).all()

