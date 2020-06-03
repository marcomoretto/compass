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
                                        version=graphene.String(required=False),
                                        database=graphene.String(required=False),
                                        normalization=graphene.String(required=False))

    ranking = graphene.Field(RankingType,
                             compendium=graphene.String(required=True),
                             version=graphene.String(required=False),
                             database=graphene.String(required=False),
                             normalization=graphene.String(required=False),
                             rank=graphene.String(required=False),
                             rank_target=graphene.String(required=True),
                             biofeatures_ids=graphene.List(of_type=graphene.ID),
                             sampleset_ids=graphene.List(of_type=graphene.ID))

    def resolve_score_rank_methods(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        score_class = cc.get_score_class(db, n)
        _module = importlib.import_module('.'.join(score_class.split('.')[:-1]))
        _class = score_class.split('.')[-1]
        _score_class = getattr(_module, _class)

        return _score_class.RANK_METHODS

    def resolve_ranking(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])
        normalization = Normalization.objects.using(db['name']).get(name=n)
        normalization_value_type = cc.get_normalized_value_name(db, normalization.name)
        value_type = ValueType.objects.using(db['name']).get(name=normalization_value_type)

        bf_ids = [i for i in kwargs.get("biofeatures_ids", [])]
        ss_ids = [i for i in kwargs.get("sampleset_ids", [])]
        if len(bf_ids):
            try:
                bf_ids = [from_global_id(i)[1] for i in bf_ids]
            except Exception as e:
                bf_ids = []
        if len(ss_ids):
            try:
                ss_ids = [from_global_id(i)[1] for i in ss_ids]
            except Exception as e:
                ss_ids = []

        score_class = cc.get_score_class(db, normalization.name)
        _module = importlib.import_module('.'.join(score_class.split('.')[:-1]))
        _class = score_class.split('.')[-1]
        _score_class = getattr(_module, _class)
        df = pd.DataFrame()

        values = NormalizedData.objects.using(db['name']).filter(
            Q(
                normalization_design_group__normalization_experiment__normalization=normalization
            ) & Q(
                value_type=value_type
            )
        )
        if kwargs['rank_target'] == 'samplesets':
            values = values.filter(Q(bio_feature__in=bf_ids))
            values = values.order_by('normalization_design_group').values_list(
                'bio_feature_id',
                'normalization_design_group',
                'value'
            )
            score = _score_class(values, bf_ids, ss_ids)
            if 'rank' in kwargs:
                rank = score.rank_sample_sets(kwargs.get('rank', None))
            else:
                rank = score.rank_sample_sets()
            df = pd.DataFrame(rank)
            df['gid'] = [to_global_id('SampleSetType', i) for i in df.index]
            df['name'] = NormalizationDesignGroup.objects.using(db['name']).filter(
                id__in=[i for i in df.index]
            ).values_list('name', flat=True)
            df['type'] = ['SampleSetType' for i in df.index]
            df = df.set_index('gid')
            df.columns = ['value', 'name', 'type']
        elif kwargs['rank_target'] == 'biofeatures':
            values = values.filter(Q(normalization_design_group_id__in=ss_ids))
            values = values.order_by('normalization_design_group').values_list(
                'bio_feature_id',
                'normalization_design_group',
                'value'
            )
            score = _score_class(values, bf_ids, ss_ids)
            rank = score.rank_biological_features(kwargs['rank'])
            df = pd.DataFrame(rank)
            df['gid'] = [to_global_id('BioFeatureType', i) for i in df.index]
            df['name'] = BioFeature.objects.using(db['name']).filter(
                id__in=[i for i in df.index]
            ).values_list('name', flat=True)
            df['type'] = ['BioFeatureType' for i in df.index]
            df = df.set_index('gid')
            df.columns = ['value', 'name', 'type']
        return df

