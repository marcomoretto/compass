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
from compass_graphql.lib.utils.module import InitModuleProxy, get_normalization_name_from_sample_set_id, \
    get_normalization_name_module_name


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
                             normalization=graphene.String(),
                             name=graphene.String(),
                             rank=graphene.String(),
                             biofeatures_ids=graphene.List(of_type=graphene.ID),
                             sampleset_ids=graphene.List(of_type=graphene.ID))

    def resolve_modules(self, info, **kwargs):

        @login_required
        def __resolve_named_modules(obj, info, **kwargs):
            compendium = kwargs['compendium']
            module_name = kwargs['name']
            conf = CompendiumConfig(compendium)
            normalization = get_normalization_name_module_name(compendium, module_name)
            plot_class = conf.get_plot_class(normalization)
            _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
            _class = plot_class.split('.')[-1]
            _plot_class = getattr(_module, _class)
            module_proxy_class = InitModuleProxy(_plot_class)
            return module_proxy_class(compendium, info.context.user, name=kwargs['name'])

        normalization = kwargs['normalization'] if 'normalization' in kwargs else None
        if normalization is None and "sampleset_ids" in kwargs:
            normalization = get_normalization_name_from_sample_set_id(kwargs['compendium'],
                                                      from_global_id(kwargs['sampleset_ids'][0])[1])
        rank = kwargs['rank'] if 'rank' in kwargs else None

        if "name" in kwargs:
            return __resolve_named_modules(self, info, **kwargs)

        conf = CompendiumConfig(kwargs['compendium'])
        plot_class = conf.get_plot_class(normalization)
        _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
        _class = plot_class.split('.')[-1]
        _plot_class = getattr(_module, _class)
        module_proxy_class = InitModuleProxy(_plot_class)

        m = module_proxy_class(kwargs['compendium'], info.context.user, normalization)
        if "biofeatures_ids" in kwargs:
            m.set_global_biofeatures(kwargs["biofeatures_ids"])
        if "sampleset_ids" in kwargs:
            m.set_global_samplesets(kwargs["sampleset_ids"])
        if len(m.biological_features) == 0:
            m.infer_biological_features(rank)
        if len(m.sample_sets) == 0:
            if normalization is None:
                raise Exception('If sample_sets is empty you need to provide a normalization for the automatic retrieval of sample_sets')
            m.infer_sample_sets(rank)
        return m
