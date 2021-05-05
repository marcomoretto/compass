import importlib
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
from rdflib import Graph
import json

from compass_graphql.lib.utils.annotation_enrichment import BioFeatureAnnotationEnrichment, SampleAnnotationEnrichment
from compass_graphql.lib.utils.compendium_config import CompendiumConfig
from compass_graphql.lib.utils.compiled_normalized_data import CompiledNormalizedData
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

        def biofeature_annotation_graph(self):
            _bf = BioFeature.objects.using(self.db['name']).filter(id__in=self.biological_features)
            g = Graph()
            for b in _bf:
                for ann in b.biofeatureannotation_set.all():
                    g.parse(data=json.dumps(ann.annotation), format='json-ld')
            return g

        def samples_annotation_graph(self):
            _ss = NormalizationDesignGroup.objects.using(self.db['name']).filter(id__in=self.sample_sets)
            g = Graph()
            for ss in _ss:
                for sample in ss.normalizationdesignsample_set.all():
                    for ann in sample.sample.sampleannotation_set.all():
                        g.parse(data=json.dumps(ann.annotation), format='json-ld')
            return g

        def get_annotation_enrichment(self, category='biofeature', p_value=0.05):
            cc = CompendiumConfig()
            ann_desc_class = cc.get_annotation_description_class(self.db, self.normalization_name)
            _module = importlib.import_module('.'.join(ann_desc_class.split('.')[:-1]))
            _class = ann_desc_class.split('.')[-1]
            _ann_desc_class = getattr(_module, _class)

            annot_enrich = {}
            if category == 'biofeature':
                for cat, term_prefix in _ann_desc_class.BIOFEATURE_ENRICHMENT_CATEGORIES.items():
                    ae = BioFeatureAnnotationEnrichment(self.db, cat, term_prefix)
                    annot_enrich[cat] = ae.get_enrichment([bf.id for bf in self.get_biological_features()], p_value)
            elif category == 'sample':
                for cat, term_prefix in _ann_desc_class.SAMPLESET_ENRICHMENT_CATEGORIES.items():
                    ae = SampleAnnotationEnrichment(self.db, cat, term_prefix)
                    samples_ids =sorted(list(set([ns.sample.id for ss in self.get_sample_sets() for ns in ss.normalizationdesignsample_set.all()])))
                    annot_enrich[cat] = ae.get_enrichment(samples_ids, p_value)

            return annot_enrich

        def get_sample_sets(self):
            _ss = {ss.id:ss for ss in NormalizationDesignGroup.objects.using(self.db['name']).filter(
                id__in=self.sample_sets
            )}
            return [_ss[i] for i in self.sample_sets]

        def get_biological_features(self):
            _bfs = {bf.id: bf for bf in BioFeature.objects.using(self.db['name']).filter(
                id__in=self.biological_features
            )}
            return [_bfs[i] for i in self.biological_features]

        def get_biological_feature_names(self):
            return [bf.name for bf in self.get_biological_features()]

        def get_sample_set_names(self):
            return [ss.name for ss in self.get_sample_sets()]

        def get_biological_feature_ids(self):
            return [bf.id for bf in self.get_biological_features()]

        def get_sample_set_ids(self):
            return [ss.id for ss in self.get_sample_sets()]

        def get_experiments_access_id(self):
            exp_acc_ids = []
            for ss in self.get_sample_sets():
                exps = set()
                for s in ss.normalizationdesignsample_set.all():
                    exps.add(s.sample.experiment.experiment_access_id)
                exp_acc_ids.append(','.join(list(exps)))
            return exp_acc_ids

        def get_platforms_access_id(self):
            plt_acc_ids = []
            for ss in self.get_sample_sets():
                plts = set()
                for s in ss.normalizationdesignsample_set.all():
                    plts.add(s.sample.platform.platform_access_id)
                plt_acc_ids.append(','.join(list(plts)))
            return plt_acc_ids

        def get_normalized_values(self):
            if self.normalized_values is None:
                norm_basename = None
                for n in self.db['normalizations']:
                    if n['name'] == self.normalization_name:
                        norm_basename = n['normalized_file_basename']
                        break
                if not norm_basename:
                    raise Exception('Cannot find normalized values')
                cnv = CompiledNormalizedData(n['normalized_file_basename'])
                self.normalized_values = cnv.df[list(self.sample_sets)].loc[list(self.biological_features)].values
                self.max = np.nanmax(cnv.df.values)
                self.min = np.nanmin(cnv.df.values)
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
            norm_basename = None
            for n in self.db['normalizations']:
                if n['name'] == self.normalization_name:
                    norm_basename = n['normalized_file_basename']
                    break
            if not norm_basename:
                raise Exception('Cannot find normalized values')
            cnv = CompiledNormalizedData(n['normalized_file_basename'])
            values = cnv.df[list(self.sample_sets)]

            score = Score(values, ss=self.sample_sets)
            score_rank = Score.RankMethods.UNCENTERED_CORRELATION if rank is None else rank
            rank = score.rank_biological_features(score_rank)
            n_bio_features = min(Module.MAX_INFER_BIOLOGICAL_FEATURE, len(self.sample_sets) * 10)
            self.biological_features = rank[:n_bio_features].index.tolist()

        def infer_sample_sets(self, rank=None):
            norm_basename = None
            for n in self.db['normalizations']:
                if n['name'] == self.normalization_name:
                    norm_basename = n['normalized_file_basename']
                    break
            if not norm_basename:
                raise Exception('Cannot find normalized values')
            cnv = CompiledNormalizedData(n['normalized_file_basename'])
            values = cnv.df.loc[list(self.biological_features)]

            score = Score(values)
            score_rank = Score.RankMethods.MAGNITUDE if rank is None else rank
            rank = score.rank_sample_sets(score_rank)
            n_sample_sets = min(Module.MAX_INFER_SAMPLE_SET, len(self.biological_features) * 10)
            self.sample_sets = rank[:n_sample_sets].index.tolist()

    return Module
