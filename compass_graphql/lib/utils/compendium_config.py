import json
import os
from django.conf import settings
import compass


class CompendiumConfig:

    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(compass.__file__)), 'compass_graphql', 'lib', 'compendia_config')
        self.compendia = []

        for file in os.listdir(self.base_dir):
            if file.endswith('.json'):
                self.compendia.append(json.loads(open(os.path.join(self.base_dir, file)).read()))

    def get_plot_class(self, db, normalization):
        for n in db['normalizations']:
            if n['name'] == normalization:
                return n['plot_class']

    def get_normalized_value_name(self, db, normalization):
        for n in db['normalizations']:
            if n['name'] == normalization:
                return n['normalized_value_name']

    def get_score_class(self, db, normalization):
        for n in db['normalizations']:
            if n['name'] == normalization:
                return n['score_class']

    def get_db_from_normalization(self, normalization):
        for c in self.compendia:
            for v in c['versions']:
                for d in v['databases']:
                    for n in d['normalizations']:
                        if n['name'] == normalization:
                            return d


    def get_db(self, compendium, version=None, database=None):
        for c in self.compendia:
            if c['name'] == compendium or c['full_name'] == compendium:
                _v = c['default_version'] if not version else version
                for v in c['versions']:
                    if str(v['version_number']) == str(_v) or str(v['version_alias']) == str(_v):
                        _db = v['default_database'] if not database else database
                        for d in v['databases']:
                            if d['name'] == _db:
                                return d
