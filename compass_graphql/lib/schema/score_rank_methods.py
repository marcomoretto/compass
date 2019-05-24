import importlib

import graphene
from django.db.models import Q
from graphene import ObjectType
from graphene.types.resolver import dict_resolver

from command.lib.db.compendium.bio_feature import BioFeature
from command.lib.db.compendium.normalization import Normalization
from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup
from command.lib.db.compendium.normalized_data import NormalizedData
from command.lib.db.compendium.value_type import ValueType
from compass_graphql.lib.utils.compendium_config import CompendiumConfig
from compass_graphql.lib.utils.score import Score

from graphql_relay import from_global_id, to_global_id
import pandas as pd
from django.conf import settings


class ScoreRankMethodsType(ObjectType):
    class Meta:
        default_resolver = dict_resolver

    sample_sets = graphene.List(graphene.String)
    biological_features = graphene.List(graphene.String)


class RankingType(ObjectType):
    id = graphene.List(graphene.ID)
    name = graphene.List(graphene.String)
    type = graphene.List(graphene.String)
    value = graphene.List(graphene.Float)

    def resolve_id(self, info, **kwargs):
        return self.index

    def resolve_name(self, info, **kwargs):
        return self['name']

    def resolve_value(self, info, **kwargs):
        return self['value']

    def resolve_type(self, info, **kwargs):
        return self['type']


class Query(object):
    score_rank_methods = graphene.Field(ScoreRankMethodsType,
                                        compendium=graphene.String(required=True),
                                        normalization=graphene.String(required=True))

    ranking = graphene.Field(RankingType,
                             compendium=graphene.String(required=True),
                             normalization=graphene.String(required=True),
                             rank=graphene.String(),
                             biofeatures_ids=graphene.List(of_type=graphene.ID),
                             sampleset_ids=graphene.List(of_type=graphene.ID))

    def resolve_score_rank_methods(self, info, **kwargs):
        conf = CompendiumConfig(kwargs['compendium'])
        normalization = kwargs['normalization'] if 'normalization' in kwargs else None
        score_class = conf.get_score_class(normalization)
        _module = importlib.import_module('.'.join(score_class.split('.')[:-1]))
        _class = score_class.split('.')[-1]
        _score_class = getattr(_module, _class)

        return _score_class.RANK_METHODS

    def resolve_ranking(self, info, compendium, **kwargs):
        conf = CompendiumConfig(compendium)
        normalization = kwargs['normalization'] if 'normalization' in kwargs else None
        normalization = Normalization.objects.using(compendium).get(name=normalization)
        normalization_value_type = conf.get_normalized_value_name(normalization.name)
        value_type = ValueType.objects.using(compendium).get(name=normalization_value_type)

        score_class = conf.get_score_class(normalization.name)
        _module = importlib.import_module('.'.join(score_class.split('.')[:-1]))
        _class = score_class.split('.')[-1]
        _score_class = getattr(_module, _class)

        if "biofeatures_ids" in kwargs:
            bf_ids = [from_global_id(i)[1] for i in kwargs["biofeatures_ids"]]
            values = NormalizedData.objects.using(compendium).filter(
                Q(
                    bio_feature__in=bf_ids
                ) & Q(
                    normalization_design_group__normalization_experiment__normalization=normalization
                ) & Q(
                    value_type=value_type
                )
            ).order_by('normalization_design_group').values_list(
                'bio_feature_id',
                'normalization_design_group',
                'value'
            )
            score = _score_class(values)
            rank = score.rank_sample_sets(kwargs['rank'])
            df = pd.DataFrame(rank)
            df['gid'] = [to_global_id('SampleSetType', i) for i in df.index]
            df['name'] = NormalizationDesignGroup.objects.using(compendium).filter(
                id__in=[i for i in df.index]
            ).values_list('name', flat=True)
            df['type'] = ['SampleSetType' for i in df.index]
            df = df.set_index('gid')
            df.columns = ['value', 'name', 'type']

        if "sampleset_ids" in kwargs:
            ss_ids = [from_global_id(i)[1] for i in kwargs["sampleset_ids"]]

            values = NormalizedData.objects.using(compendium).filter(
                Q(
                    normalization_design_group_id__in=ss_ids
                ) & Q(
                    normalization_design_group__normalization_experiment__normalization=normalization
                ) & Q(
                    value_type=value_type
                )
            ).order_by('normalization_design_group').values_list(
                'bio_feature_id',
                'normalization_design_group',
                'value'
            )
            score = _score_class(values)
            rank = score.rank_biological_features(kwargs['rank'])
            df = pd.DataFrame(rank)
            df['gid'] = [to_global_id('BioFeatureType', i) for i in df.index]
            df['name'] = BioFeature.objects.using(compendium).filter(
                id__in=[i for i in df.index]
            ).values_list('name', flat=True)
            df['type'] = ['BioFeatureType' for i in df.index]
            df = df.set_index('gid')
            df.columns = ['value', 'name', 'type']
        return df

