import pandas as pd
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
import numpy.matlib



class Score:

    class RankMethods:

        MAGNITUDE = 'magnitude'
        COEXPRESSION = 'coexpression'
        UNCENTERED_CORRELATION = 'uncentered_correlation'

    AVG_THRESHOLD = 0.33

    RANK_METHODS = {
        'sample_sets': [
            RankMethods.MAGNITUDE,
            RankMethods.COEXPRESSION
        ],
        'biological_features': [
            RankMethods.UNCENTERED_CORRELATION
        ]
    }

    def __init__(self, values, bf=None, ss=None):
        self.bf = []
        self.ss = []
        self.values = pd.DataFrame(list(values))
        if ss:
            self.ss = [int(x) for x in ss]
        if bf:
            self.bf = [int(x) for x in bf]

    def rank_biological_features(self, method=RankMethods.UNCENTERED_CORRELATION):
        if method == Score.RankMethods.UNCENTERED_CORRELATION:
            df = self.values.pivot_table(columns=self.values.columns[1], index=self.values.columns[0],
                                        values=self.values.columns[2]).reset_index()
            df = df.set_index(df.columns[0])
            if len(self.bf) == 0:
                _sv = df.mean(axis=1).abs()
                _sv = _sv[_sv > 2.0]
                self.bf = list((_sv / df.std(axis=1, ddof=1).loc[_sv.index]).sort_values().index[-3:])
            profile = np.matlib.repmat(df.loc[self.bf].mean(axis=0), df.shape[0], 1)
            isnan = np.isnan(profile) | np.isnan(df)
            profile[isnan] = np.nan
            df[isnan] = np.nan
            std_prof = np.sqrt(
                            np.divide(
                                np.nansum(np.power(profile, 2), 1),
                                np.sum(~isnan, 1)
                            )
            )
            std_data = np.sqrt(
                np.divide(
                    np.nansum(np.power(df, 2), 1),
                    np.sum(~isnan, 1)
                )
            )
            prof_data = np.multiply(df, profile)
            std_prof_data = np.multiply(std_data, std_prof)
            score = np.divide(
                        np.nansum(prof_data, 1),
                        (np.multiply(std_prof_data, np.sum(~isnan, 1)))
            )
            score = np.divide(np.multiply(score, np.sum(~isnan, 1)), isnan.shape[1])
            cs = pd.DataFrame(score)
            return cs.sort_values(by=cs.columns[0], ascending=False)[0]

    def rank_sample_sets(self, method=RankMethods.MAGNITUDE):
        if method == Score.RankMethods.MAGNITUDE:
            return self.values[2].groupby(self.values[1]).apply(lambda x: np.mean(abs(x))).sort_values(ascending=False)
        elif method == Score.RankMethods.COEXPRESSION:
            group = self.values[2].groupby(self.values[1])
            return ((group.mean().abs() - Score.AVG_THRESHOLD) / group.std()).sort_values(ascending=False)
        return None
