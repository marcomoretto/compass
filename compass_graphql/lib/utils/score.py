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
        self.values = values
        if ss:
            self.ss = [int(x) for x in ss]
        if bf:
            self.bf = [int(x) for x in bf]

    def rank_biological_features(self, method=RankMethods.UNCENTERED_CORRELATION):
        if method == Score.RankMethods.UNCENTERED_CORRELATION:
            df = self.values
            pos_idx = 2
            neg_idx = 2
            tot_idx = pos_idx + neg_idx
            if len(self.bf) == 0:
                _sv = df.mean(axis=1).abs()
                _sv = _sv[_sv > 2.0]
                _sv = (_sv / df.std(axis=1, ddof=1).loc[_sv.index]).sort_values(ascending=False).dropna()
                for g in _sv.index:
                    if df.loc[g].isnull().sum() <= np.round(len(df.columns) * 0.2):
                        if df.loc[g].mean() >= 0 and pos_idx:
                            pos_idx -= 1
                            self.bf.append(g)
                        elif df.loc[g].mean() < 0 and neg_idx:
                            neg_idx -= 1
                            self.bf.append(g)
                    if len(self.bf) >= tot_idx:
                        break
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
            nan_allowed_fun = lambda x : np.exp(-x / 2)
            return (self.values.abs().mean(axis=0) * np.isnan(self.values).sum(axis=0).apply(nan_allowed_fun)).sort_values(ascending=False)
        elif method == Score.RankMethods.COEXPRESSION:
            return ((self.values.mean(axis=0).abs() - Score.AVG_THRESHOLD) / self.values.std(axis=0)).sort_values(ascending=False)
        return None
