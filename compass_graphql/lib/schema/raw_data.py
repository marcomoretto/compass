import graphene
from django.db.models import Q
from graphene import ObjectType
from graphene_django.filter import DjangoFilterConnectionField

from command.lib.db.compendium.sample import Sample
from graphql_relay import from_global_id

from command.lib.db.compendium.raw_data import RawData

from command.lib.db.compendium.bio_feature import BioFeature

from command.lib.db.compendium.bio_feature_reporter import BioFeatureReporter

from command.lib.db.compendium.value_type import ValueType
from compass_graphql.lib.schema.bio_feature import BioFeatureType
from compass_graphql.lib.schema.sample import SampleType
from compass_graphql.lib.utils.compendium_config import CompendiumConfig


class ProxyRawDataType(ObjectType):
    sample = DjangoFilterConnectionField(SampleType, compendium=graphene.String())
    biofeatures = DjangoFilterConnectionField(BioFeatureType, compendium=graphene.String())
    biofeature_reporters = graphene.List(of_type=graphene.String)
    value_types = graphene.List(of_type=graphene.String)
    values = graphene.List(of_type=graphene.Float)

    def resolve_sample(self, info, **kwargs):
        return self['sample']

    def resolve_values(self, info, **kwargs):
        return self['values']

    def resolve_biofeatures(self, info, **kwargs):
        return self['biofeatures']

    def resolve_biofeature_reporters(self, info, **kwargs):
        return [bfr.name for bfr in self['biofeature_reporters']]

    def resolve_value_types(self, info, **kwargs):
        return [vt.description for vt in self['value_types']]

class Query(object):
    raw_data = graphene.Field(ProxyRawDataType,
                             compendium=graphene.String(required=True),
                             version=graphene.String(required=False),
                             database=graphene.String(required=False),
                             normalization=graphene.String(required=False),
                             sample_name=graphene.String(required=False),
                             sample_id=graphene.ID(required=False)
                            )

    def resolve_raw_data(self, info, **kwargs):
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        n = kwargs.get('normalization', db['default_normalization'])

        if 'sample_id' in kwargs:
            sample_id = from_global_id(kwargs['sample_id'])
            if not sample_id[0] == 'SampleType':
                raise Exception("Not a valid sample_id")
            sample = Sample.objects.using(db['name']).get(id=sample_id[1])
        elif 'sample_name' in kwargs:
            sample = Sample.objects.using(db['name']).get(sample_name=kwargs['sample_name'])
        else:
            raise Exception('You need to provide a valid sample_id or a valid sample_name')
        rd = RawData.objects.using(db['name']).filter(
            Q(sample=sample)&
            Q(bio_feature_reporter__bio_feature__isnull=False))
        rd = list(zip(*rd.values_list('bio_feature_reporter__bio_feature__id', 'bio_feature_reporter_id', 'value_type_id', 'value')))
        biofeatures = {bf.id: bf for bf in BioFeature.objects.using(db['name']).filter(id__in=rd[0])}
        sorted_biofeatures = [biofeatures[id] for id in rd[0]]
        biofeature_reporters = {bfr.id: bfr for bfr in BioFeatureReporter.objects.using(db['name']).filter(id__in=rd[1])}
        sorted_biofeature_reporters = [biofeature_reporters[id] for id in rd[1]]
        value_types = {vt.id: vt for vt in
                                ValueType.objects.using(db['name']).filter(id__in=rd[2])}
        sorted_value_types = [value_types[id] for id in rd[2]]

        proxy = {
            'biofeatures': sorted_biofeatures,
            'biofeature_reporters': sorted_biofeature_reporters,
            'value_types': sorted_value_types,
            'values': rd[3],
            'sample': [sample]
        }

        return proxy