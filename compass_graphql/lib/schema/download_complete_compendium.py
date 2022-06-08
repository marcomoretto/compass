import graphene
from graphene import ObjectType
from graphql_relay import to_global_id
from compass_graphql.lib.utils.compendium_config import CompendiumConfig
import os
from django.contrib.staticfiles.templatetags.staticfiles import static
from compass_graphql.lib.utils.compiled_normalized_data import CompiledNormalizedData


class CompleteCompendiumUrlType(ObjectType):

    static_filename = graphene.String()

    def resolve_static_filename(self, info, **kwargs):
        return static(self)


class Query(object):
    whole_compendium = graphene.Field(CompleteCompendiumUrlType,
                                         compendium=graphene.String(required=True),
                                         version=graphene.String(required=False),
                                         database=graphene.String(required=False),
                                         normalization=graphene.String(required=False)
                                         )

    def resolve_whole_compendium(self, info, **kwargs):
        norm_basename = None
        cc = CompendiumConfig()
        db = cc.get_db(
            kwargs['compendium'],
            kwargs.get('version', None),
            kwargs.get('database', None)
        )
        normalization_name = kwargs.get('normalization', db['default_normalization'])
        # read normalization
        for n in db['normalizations']:
            if n['name'] == normalization_name:
                norm_basename = n['normalized_file_basename']
                break
        if not norm_basename:
            raise Exception('Cannot find normalized values')
        fn = norm_basename.replace('/', '_') + '.csv.zip'
        if not os.path.exists(os.path.join('static', fn)):
            cnv = CompiledNormalizedData(norm_basename)
            columns = {c: to_global_id('SampleSetType', c) for c in cnv.df.columns.tolist()}
            idx = {b: to_global_id('BioFeatureType', b) for b in cnv.df.index.tolist()}
            df = cnv.df.rename(columns=columns, index=idx)
            df.to_csv(os.path.join('static', fn), compression='zip')

        return fn
