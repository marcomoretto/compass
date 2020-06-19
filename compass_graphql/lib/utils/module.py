import itertools

from django.conf import settings
from django.db.models import Min, Max
from django.db.models import Q
from graphql_relay import from_global_id

from command.lib.db.compendium.bio_feature import BioFeature
from command.lib.db.compendium.normalization import Normalization
from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup
from command.lib.db.compendium.normalization_design_sample import NormalizationDesignSample
from command.lib.db.compendium.normalized_data import NormalizedData
from command.lib.db.compendium.value_type import ValueType

import numpy as np

from compass_graphql.lib.utils.compendium_config import CompendiumConfig
from compass_graphql.lib.utils.score import Score
from compass_graphql.lib.db.module import Module as ModuleDB, Module


def get_normalization_name_from_sample_set_id(db, sample_set_id):
    ss = NormalizationDesignGroup.objects.using(db['name']).get(id=int(sample_set_id))
    return ss.normalization_experiment.normalization.name


def InitModuleProxy(plot_class):

    class Module(plot_class):

        MAX_INFER_SAMPLE_SET = 300
        MAX_INFER_BIOLOGICAL_FEATURE = 300

        def __init__(self, db, user, normalization=None, biological_features=tuple(), sample_sets=tuple()):
            self.db = db
            self.user = user
            self.normalization_name = normalization
            self.biological_features = tuple(biological_features)
            self.sample_sets = tuple(sample_sets)
            self.normalized_values = None
            self.max = 2
            self.min = -2

        @property
        def normalization(self):
            if self.normalization_name is None:
                if len(self.sample_sets) > 0:
                    sample_set = NormalizationDesignGroup.objects.using(self.compendium).get(
                        id=self.sample_sets[0]
                    )
                    self.normalization_name = sample_set.normalization_experiment.normalization.name
            return self.normalization_name

        def get_sample_sets(self):
            return NormalizationDesignGroup.objects.using(self.db['name']).filter(
                id__in=self.sample_sets
            )

        def get_biological_features(self):
            return BioFeature.objects.using(self.db['name']).filter(
                id__in=self.biological_features
            )

        def get_biological_feature_names(self):
            return list(BioFeature.objects.using(self.db['name']).filter(id__in=self.biological_features).values_list('name', flat=True))

        def get_sample_set_names(self):
            return list(NormalizationDesignGroup.objects.using(self.db['name']).filter(id__in=self.sample_sets).values_list('name', flat=True))

        def get_normalized_values(self):
            if self.normalized_values is None:
                bf_num = len(self.biological_features)
                ss_num = len(self.sample_sets)
                cc = CompendiumConfig()
                normalization_value_type = cc.get_normalized_value_name(self.db, self.normalization)
                m_value_type = ValueType.objects.using(self.db['name']).get(name=normalization_value_type)
                self.min = -8 #_min_max['value__min']
                self.max = 8 #_min_max['value__max']
                _norm_data = NormalizedData.objects.using(self.db['name']).filter(
                    value_type=m_value_type,
                    bio_feature_id__in=self.biological_features,
                    normalization_design_group_id__in=self.sample_sets
                )
                values = list(_norm_data.order_by('bio_feature_id', 'normalization_design_group_id').values_list(
                    'bio_feature_id', 'normalization_design_group_id', 'value')
                )
                values_ids = {(v[0], v[1]) for v in values}
                missing_values = set(itertools.product(self.biological_features, self.sample_sets)) - values_ids
                for mv in missing_values:
                    values.append((mv[0], mv[1], np.NaN))
                values.sort(key=lambda x: (x[0], x[1]))
                self.normalized_values = np.array([x[2] for x in values]).reshape(
                    bf_num, ss_num
                )
                self.biological_features = tuple(dict.fromkeys(np.array([x[0] for x in values])))
                self.sample_sets = tuple(dict.fromkeys(np.array([x[1] for x in values])))
            return self.normalized_values

        def set_global_biofeatures(self, bf_local_ids):
            bf_ids = []
            for bf in bf_local_ids:
                lid = from_global_id(bf)
                if lid[0] != 'BioFeatureType':
                    raise Exception("You should provide valid Biological Feature ids")
                bf_ids.append(int(lid[1]))
            self.biological_features = tuple(bf_ids)

        def set_global_samplesets(self, ss_local_ids):
            ss_ids = []
            for ss in ss_local_ids:
                lid = from_global_id(ss)
                if lid[0] != 'SampleSetType':
                    raise Exception("You should provide valid Sample Set ids")
                ss_ids.append(int(lid[1]))
            self.sample_sets = tuple(ss_ids)

        def infer_biological_features(self, rank=None):
            cc = CompendiumConfig()
            normalization_value_type = cc.get_normalized_value_name(self.db, self.normalization)
            value_type = ValueType.objects.using(self.db['name']).get(name=normalization_value_type)
            normalization = Normalization.objects.using(self.db['name']).get(name=self.normalization)
            values = NormalizedData.objects.using(self.db['name']).filter(
                Q(
                    normalization_design_group__in=self.sample_sets
                )  & Q(
                    normalization_design_group__normalization_experiment__normalization=normalization
                ) & Q(
                    value_type=value_type
                )
            ).order_by('normalization_design_group').values_list(
                'bio_feature_id',
                'normalization_design_group',
                'value'
            )
            score = Score(values, ss=self.sample_sets)
            score_rank = Score.RankMethods.UNCENTERED_CORRELATION if rank is None else rank
            rank = score.rank_biological_features(score_rank)
            n_bio_features = min(Module.MAX_INFER_BIOLOGICAL_FEATURE, len(self.sample_sets) * 10)
            self.biological_features = rank[:n_bio_features].index.tolist()

        def infer_sample_sets(self, rank=None):
            cc = CompendiumConfig()
            normalization_value_type = cc.get_normalized_value_name(self.db, self.normalization)
            value_type = ValueType.objects.using(self.db['name']).get(name=normalization_value_type)
            normalization = Normalization.objects.using(self.db['name']).get(name=self.normalization)
            values = NormalizedData.objects.using(self.db['name']).filter(
                Q(
                    bio_feature__in=self.biological_features
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
            score = Score(values)
            score_rank = Score.RankMethods.MAGNITUDE if rank is None else rank
            rank = score.rank_sample_sets(score_rank)
            n_sample_sets = min(Module.MAX_INFER_SAMPLE_SET, len(self.biological_features) * 10)
            self.sample_sets = rank[:n_sample_sets].index.tolist()

    return Module
