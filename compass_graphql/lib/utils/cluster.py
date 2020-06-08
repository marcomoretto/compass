import numpy as np
import scipy as sp
from scipy import spatial, cluster
from sklearn.cluster import SpectralClustering, SpectralCoclustering, SpectralBiclustering
from sklearn.metrics import silhouette_score
import pandas as pd


class Cluster:

    class ClusterMethods:
        EXPRESSION = 'expression'
        EXPERIMENT = 'experiment'

    def __init__(self, data, max=None, min=None):
        self.data = data
        self.max = np.nanmax(self.data) if not max else max
        self.min = np.nanmin(self.data) if not min else min

    def _get_cluster(self, method='expression'):
        data = np.nan_to_num(self.data)
        model = SpectralBiclustering()
        model.fit(data)
        sorted_data = self.data[np.argsort(model.row_labels_)]
        sorted_data = sorted_data[:, np.argsort(model.column_labels_)]
        return sorted_data

    def get_cluster(self, method='expression', max_nr_c=99, fail_tol=10, nan_frac=.75, predef_obs=[2.5, -2.5]):
        coexpr_cutoff = 0.75
        max_nr_c = 3 + np.floor(self.data.shape[0] / 10)
        fail_tol_g = min(fail_tol, max_nr_c + len(predef_obs))
        cg, g, i_ug, pdmg = self._optimal_h_clust(np.copy(self.data), max_nr_c, fail_tol_g, nan_frac, predef_obs)
        max_nr_c = 3 + np.floor(self.data.shape[1] / 10)
        fail_tol_g = min(fail_tol, max_nr_c + len(predef_obs))
        cc, c, i_uc, pdmc = self._optimal_h_clust(np.copy(self.data.T), max_nr_c, fail_tol_g, nan_frac, predef_obs)
        sorted_data = self.data[g]
        sorted_data = sorted_data[:, c]
        return sorted_data, cg, cc, g, c

    def _optimal_h_clust(self, data, max_nr_c, fail_tol, nan_frac, predef_obs):
        i_nan = (np.sum(np.isnan(data), axis=1) / data.shape[1]) > nan_frac
        max_nr_c = data.shape[0] if max_nr_c is None else max_nr_c
        nr_c = 2
        if predef_obs is not None and len(predef_obs) > 0:
            nr_c = len(predef_obs)
            max_nr_c = nr_c if max_nr_c < nr_c else max_nr_c + nr_c
            for predef_ob in predef_obs:
                data = np.vstack([data, [predef_ob] * data.shape[1]])
        data = np.where(np.isnan(data.T), np.ma.array(data.T, mask=np.isnan(data.T)).mean(axis=0), data.T).T
        _data = np.copy(data)
        x_norm = np.sqrt(np.sum(data**2, 1))
        hi = x_norm > np.finfo(data.dtype).eps
        lo = np.logical_not(x_norm <= np.finfo(data.dtype).eps)
        data = data[lo]
        max_nr_c = min(max_nr_c, data.shape[0])
        data = np.array(pd.DataFrame(data).dropna())
        dist = spatial.distance.pdist(data, metric='cosine')
        tree = cluster.hierarchy.linkage(dist, method='average')
        i_ud_new = cluster.hierarchy.fcluster(tree, nr_c + 1, criterion='maxclust')
        i_ud = i_ud_new
        s_new = silhouette_score(data, i_ud_new, metric='cosine')
        s = 0
        while s_new > s and nr_c < max_nr_c:
            s = s_new
            i_ud = i_ud_new
            nr_c += 1
            i_ud_new = cluster.hierarchy.fcluster(tree, nr_c + 1, criterion='maxclust')
            s_new = silhouette_score(data, i_ud_new, metric='cosine')
            if s_new <= s:
                t = 1
                while t <= fail_tol and s_new <= s:
                    t += 1
                    i_ud_new = cluster.hierarchy.fcluster(tree, nr_c + t, criterion='maxclust')
                    s_new = silhouette_score(data, i_ud_new, metric='cosine')
                    if s_new > s:
                        nr_c = nr_c + t - 1
                        break
        opt_d = cluster.hierarchy.leaves_list(cluster.hierarchy.optimal_leaf_ordering(tree, dist))
        idxs = list(range(data.shape[0]))
        opt_d_unique_sorted, opt_d_idx = np.unique(opt_d, return_index=True)
        tmp = np.in1d(opt_d_unique_sorted, idxs, assume_unique=True)
        s_ud = opt_d_idx[tmp]
        cls = np.zeros(_data.shape[0])
        opt = np.zeros(_data.shape[0])
        cls[hi] = i_ud
        opt[hi] = s_ud
        mask = np.array([hi if x else [False] * len(hi) for x in hi])
        pdm = np.zeros((_data.shape[0], _data.shape[0]))
        pdm[mask] = spatial.distance.squareform(dist).flatten()
        pdm = pdm.reshape((_data.shape[0], _data.shape[0]))
        i_nan_lo = np.concatenate((np.where(i_nan)[0], np.where(np.logical_not(lo))[0]))
        cls[i_nan_lo] = np.max(cls) + 1
        if predef_obs:
            cls = cls[:-len(predef_obs)]
            opt = opt[:-len(predef_obs)]
            pdm = pdm[:-len(predef_obs), :-len(predef_obs)]
        if np.max(cls) + 1 > len(np.unique(cls)):
            u, _tmp, i = np.unique(cls, return_index=True, return_inverse=True)
            c = np.array(range(len(u)))
            cls = c[i]
        cd = np.sort(np.array([cls, opt]))[0]
        d = np.argsort(np.array([cls, opt]), axis=1)[0]

        return cd, d, cls, pdm
