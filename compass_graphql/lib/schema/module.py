import importlib

import graphene
from graphene import ObjectType
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required
from graphql_relay import from_global_id

from compass_graphql.lib.schema.bio_feature import BioFeatureType
from compass_graphql.lib.schema.sample_set import SampleSetType
from compass_graphql.lib.utils.compendium_config import CompendiumConfig
from compass_graphql.lib.utils.module import InitModuleProxy, get_normalization_name_from_sample_set_id


class ProxyModuleType(ObjectType):
    normalization = graphene.String()
    normalized_values = graphene.List(graphene.List(of_type=graphene.Float))
    biofeatures = DjangoFilterConnectionField(BioFeatureType, compendium=graphene.String())
    sample_sets = DjangoFilterConnectionField(SampleSetType,
                                              compendium=graphene.String(),
                                              samples=graphene.List(of_type=graphene.ID))

    def resolve_normalization(self, info, **kwargs):
        return self.normalization

    def resolve_sample_sets(self, info, **kwargs):
        return self.get_sample_sets()

    def resolve_biofeatures(self, info, **kwargs):
        return self.get_biological_features()

    def resolve_normalized_values(self, info):
        return self.get_normalized_values()


class Query(object):
    modules = graphene.Field(ProxyModuleType,
                             compendium=graphene.String(required=True),
                             version=graphene.String(required=False),
                             database=graphene.String(required=False),
                             normalization=graphene.String(required=False),
                             rank=graphene.String(),
                             biofeatures_ids=graphene.List(of_type=graphene.ID),
                             sampleset_ids=graphene.List(of_type=graphene.ID))

    def resolve_modules(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        if "sampleset_ids" in kwargs:
            n = get_normalization_name_from_sample_set_id(db, from_global_id(kwargs['sampleset_ids'][0])[1])
            db = cc.get_db_from_normalization(n)
        else:
            n = kwargs.get('normalization', db['default_normalization'])
        rank = kwargs['rank'] if 'rank' in kwargs else None
        plot_class = cc.get_plot_class(db, n)
        _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
        _class = plot_class.split('.')[-1]
        _plot_class = getattr(_module, _class)
        module_proxy_class = InitModuleProxy(_plot_class)

        m = module_proxy_class(db, info.context.user, n)
        if "biofeatures_ids" in kwargs:
            m.set_global_biofeatures(kwargs["biofeatures_ids"])
        if "sampleset_ids" in kwargs:
            m.set_global_samplesets(kwargs["sampleset_ids"])
        if len(m.biological_features) == 0:
            m.infer_biological_features(rank)
        if len(m.sample_sets) == 0:
            if n is None:
                raise Exception('If sample_sets is empty you need to provide a normalization for the automatic retrieval of sample_sets')
            m.infer_sample_sets(rank)
        return m
