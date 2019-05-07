import json
import os
from django.conf import settings


class CompendiumConfig:

    def __init__(self, compendium_nick_name):
        self._compendium_nick_name = compendium_nick_name
        self._json_file = os.path.join(settings.BASE_DIR, 'compass_graphql', 'lib', 'normalization_config', compendium_nick_name + '.json')

    def get_config(self):
        with open(self._json_file) as f:
            return {
                self._compendium_nick_name: json.load(f)
            }

    def get_normalization_names(self):
        return [norm['name'] for norm in self.get_config()[self._compendium_nick_name]['normalizations']]

    def get_plot_class(self, normalization_name):
        for norm in self.get_config()[self._compendium_nick_name]['normalizations']:
            if norm['name'] == normalization_name:
                return norm['plot_class']

    def get_score_class(self, normalization_name):
        for norm in self.get_config()[self._compendium_nick_name]['normalizations']:
            if norm['name'] == normalization_name:
                return norm['score_class']

    def get_description(self):
        return self.get_config()[self._compendium_nick_name]['description']

    def get_full_name(self):
        return self.get_config()[self._compendium_nick_name]['full_name']

    def get_normalized_value_name(self, normalization_name):
        for norm in self.get_config()[self._compendium_nick_name]['normalizations']:
            if norm['name'] == normalization_name:
                return norm['normalized_value_name']

