import json
import os
from django.conf import settings
import compass
from command.lib.db.compendium.normalization import Normalization


class CompendiumConfig:

    def __init__(self):
        self.base_dir = os.path.join(os.path.dirname(os.path.dirname(compass.__file__)), 'compass_graphql', 'lib', 'compendia_config')
        self.compendia = []

        for file in os.listdir(self.base_dir):
            if file.endswith('.json'):
                self.compendia.append(json.loads(open(os.path.join(self.base_dir, file)).read()))

        for c in self.compendia:
            _v_to_remove = []
            for v in c['versions']:
                _d_to_remove = []
                for d in v['databases']:
                    norm = []
                    for n in d['normalizations']:
                        _n = Normalization.objects.using(d['name']).filter(name=n['name']).first()
                        if not _n or not _n.is_public:
                            continue
                        norm.append(n['name'])
                    if len(norm) == 0:
                        _d_to_remove.append(d)
                for _d in _d_to_remove:
                    v['databases'].remove(_d)
                if len(v['databases']) == 0:
                    _v_to_remove.append(v)
            for _v in _v_to_remove:
                c['versions'].remove(_v)

    def get_annotation_description_class(self, db, normalization):
        for n in db['normalizations']:
            if n['name'] == normalization:
                return n['annot_description_class']

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
