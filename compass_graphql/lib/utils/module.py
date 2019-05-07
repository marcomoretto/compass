import itertools

from django.conf import settings
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


def get_normalization_name_from_sample_set_id(compendium, sample_set_id):
    ss = NormalizationDesignGroup.objects.using(compendium).get(id=int(sample_set_id))
    return ss.normalization_experiment.normalization.name


def get_normalization_name_module_name(compendium, module_name):
    m = Module.objects.get(name=module_name)
    n = NormalizedData.objects.using(compendium).get(id=m.moduledata_set.all()[0].normalizeddata_id)
    return n.normalization_design_group.normalization_experiment.normalization.name


def InitModuleProxy(plot_class):

    class Module(plot_class):

        MAX_INFER_SAMPLE_SET = 300

        def __init__(self, compendium, user, normalization=None, biological_features=[], sample_sets=[], name=None):
            self.compendium = compendium
            self.user = user
            self.normalization_name = normalization
            self.biological_features = biological_features
            self.sample_sets = sample_sets
            self.name = name
            self.normalized_values = None

        @property
        def normalization(self):
            if self.normalization_name is None:
                if self.name:
                    m = ModuleDB.objects.using('default').get(user=self.user,
                                                    compendium_nick_name=self.compendium,
                                                    name=self.name)
                    data = NormalizedData.objects.using(self.compendium).get(
                        id=m.moduledata_set.all()[0].normalizeddata_id
                    )
                    self.normalization_name = data.normalization_design_group.normalization_experiment.normalization.name
                elif len(self.sample_sets) > 0:
                    sample_set = NormalizationDesignGroup.objects.using(self.compendium).get(
                        id=self.sample_sets[0]
                    )
                    self.normalization_name = sample_set.normalization_experiment.normalization.name
            return self.normalization_name

        def get_sample_sets(self):
            if self.name:
                m = ModuleDB.objects.using('default').get(user=self.user,
                                                    compendium_nick_name=self.compendium,
                                                    name=self.name)
                self.sample_sets = list(NormalizedData.objects.using(self.compendium).filter(
                    id__in=[mds.normalizeddata_id for mds in m.moduledata_set.all()]
                ).values_list('normalization_design_group_id', flat=True))
            return NormalizationDesignGroup.objects.using(self.compendium).filter(
                id__in=self.sample_sets
            ).order_by("id")

        def get_biological_features(self):
            if self.name:
                m = ModuleDB.objects.using('default').get(user=self.user,
                                                        compendium_nick_name=self.compendium,
                                                        name=self.name)
                self.biological_features = list(NormalizedData.objects.using(self.compendium).filter(
                    id__in=[mds.normalizeddata_id for mds in m.moduledata_set.all()]
                ).values_list('bio_feature_id', flat=True))
            return BioFeature.objects.using(self.compendium).filter(
                id__in=self.biological_features
            ).order_by("id")

        def get_biological_feature_names(self):
            return list(BioFeature.objects.using(self.compendium).filter(id__in=self.biological_features).values_list('name', flat=True))

        def get_sample_set_names(self):
            return list(NormalizationDesignGroup.objects.using(self.compendium).filter(id__in=self.sample_sets).values_list('name', flat=True))

        def get_normalized_values(self):
            if self.normalized_values is None:
                bf_num = len(self.biological_features)
                ss_num = len(self.sample_sets)
                if self.name:
                    m = ModuleDB.objects.using('default').get(user=self.user,
                                                           compendium_nick_name=self.compendium,
                                                           name=self.name)
                    values = list(NormalizedData.objects.using(self.compendium).filter(
                        id__in=[mds.normalizeddata_id for mds in m.moduledata_set.all()]
                    ).order_by('bio_feature_id', 'normalization_design_group_id').values_list(
                        'bio_feature_id', 'normalization_design_group_id', 'value')
                    )
                    for v in values:
                        if v[0] not in self.biological_features:
                            self.biological_features.append(v[0])
                        if v[1] not in self.sample_sets:
                            self.sample_sets.append(v[1])
                    bf_num = m.biological_features_num
                    ss_num = m.sample_sets_num
                    values_ids = {(v[0], v[1]) for v in values}
                    missing_values = set(itertools.product(self.biological_features, self.sample_sets)) - values_ids
                    for mv in missing_values:
                        values.append((mv[0], mv[1], np.NaN))
                else:
                    conf = CompendiumConfig(self.compendium)
                    normalization_value_type = conf.get_normalized_value_name(self.normalization_name)
                    m_value_type = ValueType.objects.using(self.compendium).get(name=normalization_value_type)
                    values = list(NormalizedData.objects.using(self.compendium).filter(
                        value_type=m_value_type,
                        bio_feature_id__in=self.biological_features,
                        normalization_design_group_id__in=self.sample_sets
                    ).order_by('bio_feature_id', 'normalization_design_group_id').values_list(
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
            return self.normalized_values

        def set_global_biofeatures(self, bf_local_ids):
            bf_ids = []
            for bf in bf_local_ids:
                lid = from_global_id(bf)
                if lid[0] != 'BioFeatureType':
                    raise Exception("You should provide valid Biological Feature ids")
                bf_ids.append(int(lid[1]))
            self.biological_features = bf_ids

        def set_global_samplesets(self, ss_local_ids):
            ss_ids = []
            for ss in ss_local_ids:
                lid = from_global_id(ss)
                if lid[0] != 'SampleSetType':
                    raise Exception("You should provide valid Sample Set ids")
                ss_ids.append(int(lid[1]))
            self.sample_sets = ss_ids

        def infer_biological_features(self, rank=None):
            conf = CompendiumConfig(self.compendium)
            normalization_value_type = conf.get_normalized_value_name(self.normalization_name)
            value_type = ValueType.objects.using(self.compendium).get(name=normalization_value_type)
            NormalizedData.objects.using(self.compendium).filter(
                Q(
                    normalization_design_group__in=self.sample_sets
                ) & Q(
                    value_type=value_type
                )
            )

        def infer_sample_sets(self, rank=None):
            normalization = Normalization.objects.using(self.compendium).get(name=self.normalization)
            conf = CompendiumConfig(self.compendium)
            normalization_value_type = conf.get_normalized_value_name(self.normalization_name)
            value_type = ValueType.objects.using(self.compendium).get(name=normalization_value_type)
            values = NormalizedData.objects.using(self.compendium).filter(
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
