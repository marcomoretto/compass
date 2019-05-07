import graphene
from django.conf import settings
from django.db import transaction
from graphene import Mutation
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from graphql_jwt.decorators import login_required

from compass_graphql.lib.db.module import Module
from graphql_relay.node.node import from_global_id, to_global_id

from compass_graphql.lib.db.module_data import ModuleData

from command.lib.db.compendium.normalized_data import NormalizedData
from command.lib.db.compendium.value_type import ValueType
from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class ModuleType(DjangoObjectType):
    class Meta:

        model = Module
        filter_fields = {
            'name': ['exact', 'icontains', 'istartswith', 'in'],
            'compendium_nick_name': ['exact', 'icontains', 'istartswith'],
        }
        interfaces = (graphene.relay.Node,)


class UpdateModuleName(Mutation):
    class Arguments:
        compendium = graphene.String(required=True)
        old_name = graphene.String(required=True)
        new_name = graphene.String(required=True)

    ok = graphene.Boolean()
    module = graphene.Field(ModuleType)

    @login_required
    def mutate(self, info, compendium, old_name, new_name):
        module = Module.objects.get(compendium_nick_name=compendium, name=old_name, user=info.context.user)
        module.name = new_name
        module.save()
        return UpdateModuleName(module=module, ok=True)


class DeleteModule(Mutation):
    class Arguments:
        compendium = graphene.String(required=True)
        name = graphene.String(required=True)

    ok = graphene.Boolean()
    module = graphene.Field(ModuleType)

    @login_required
    def mutate(self, info, compendium, name):
        module = Module.objects.get(compendium_nick_name=compendium, name=name, user=info.context.user)
        module.delete()
        return DeleteModule(module=module, ok=True)


class SaveModule(Mutation):
    class Arguments:
        compendium = graphene.String(required=True)
        name = graphene.String(required=True)
        biofeatures_ids = graphene.List(of_type=graphene.ID, required=True)
        sampleset_ids = graphene.List(of_type=graphene.ID, required=True)

    id = graphene.ID()
    ok = graphene.Boolean()
    module = graphene.Field(ModuleType)

    @login_required
    def mutate(self, info, compendium, name, biofeatures_ids, sampleset_ids):
        bf_ids = []
        ss_ids = []
        for bf in biofeatures_ids:
            lid = from_global_id(bf)
            if lid[0] != 'BioFeatureType':
                raise Exception("You should provide valid Biological Feature ids")
            bf_ids.append(lid[1])
        for ss in sampleset_ids:
            lid = from_global_id(ss)
            if lid[0] != 'SampleSetType':
                raise Exception("You should provide valid Sample Set ids")
            ss_ids.append(lid[1])
        values = NormalizedData.objects.using(compendium).filter(
            bio_feature_id__in=bf_ids,
            normalization_design_group_id__in=ss_ids
        ).order_by('bio_feature_id', 'normalization_design_group_id').values_list('id', flat=True)
        with transaction.atomic():
            try:
                module = Module.objects.get(compendium_nick_name=compendium,
                                   name=name,
                                   user=info.context.user)
                module.moduledata_set.all().delete()
            except Exception as e:
                module = Module(compendium_nick_name=compendium,
                                name=name,
                                user=info.context.user)
            module.biological_features_num=len(bf_ids)
            module.sample_sets_num=len(ss_ids)
            module.save()
            data = [ModuleData(module=module, normalizeddata_id=v) for v in values]
            ModuleData.objects.bulk_create(data)
            ok = True
            id = to_global_id('ModuleType', module.id)
        return SaveModule(module=module, ok=ok, id=id)


class Query(object):
    search_modules = DjangoFilterConnectionField(ModuleType, compendium=graphene.String(required=True))

    @login_required
    def resolve_search_modules(self, info, **kwargs):
        return Module.objects.using('default').filter(user=info.context.user, compendium_nick_name=kwargs['compendium'])
