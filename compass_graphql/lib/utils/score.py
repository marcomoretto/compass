import pandas as pd
import numpy as np


class Score:

    class RankMethods:

        MAGNITUDE = 'magnitude'
        COEXPRESSION = 'coexpression'
        STANDARD_DEVIATION = 'std'

    AVG_THRESHOLD = 0.33

    RANK_METHODS = {
        'sample_sets': [
            RankMethods.MAGNITUDE,
            RankMethods.COEXPRESSION
        ],
        'biological_features': [
            RankMethods.STANDARD_DEVIATION
        ]
    }

    def __init__(self, values):
        self.values = pd.DataFrame(list(values))

    def rank_biological_features(self, method=RankMethods.STANDARD_DEVIATION):
        if method == Score.RankMethods.STANDARD_DEVIATION:
            return self.values[2].groupby(self.values[0]).apply(lambda x: np.sqrt(np.sum(x**2) / float(len(x)))).sort_values(ascending=False)

    def rank_sample_sets(self, method=RankMethods.MAGNITUDE):
        if method == Score.RankMethods.MAGNITUDE:
            return self.values[2].groupby(self.values[1]).apply(lambda x: np.mean(abs(x))).sort_values(ascending=False)
        elif method == Score.RankMethods.COEXPRESSION:
            return ((self.values[2].groupby(self.values[1]).mean().abs() -Score.AVG_THRESHOLD) / self.values[2].groupby(self.values[1]).std()).sort_values(ascending=False)
        return None
