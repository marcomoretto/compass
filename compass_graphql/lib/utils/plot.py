import json

import plotly.graph_objs as go
import plotly.figure_factory as ff
import numpy as np
import pandas as pd
from django.db.models import Q
from graphql_relay import to_global_id
from plotly import tools
import networkx as nx

from command.lib.db.compendium.normalization import Normalization
from command.lib.db.compendium.normalized_data import NormalizedData
from command.lib.db.compendium.value_type import ValueType

from command.lib.db.compendium.bio_feature import BioFeature

from command.lib.db.compendium.normalization_design_group import NormalizationDesignGroup
from compass_graphql.lib.utils.cluster import Cluster
from compass_graphql.lib.utils.compendium_config import CompendiumConfig
from compass_graphql.lib.utils.compiled_normalized_data import CompiledNormalizedData
from compass_graphql.lib.utils.score import Score


class Plot:

    class PlotType:

        SAMPLE_SETS_MAGNITUDE_DISTRIBUTION = 'sample_sets_magnitude_distribution'
        SAMPLE_SETS_COEXPRESSION_DISTRIBUTION = 'sample_sets_coexpression_distribution'
        BIOFEATURES_UNCENTERED_CORRELATION_DISTRIBUTION = 'biological_features_uncentered_correlation_distribution'
        MODULE_HEATMAP_EXPRESSION = 'module_heatmap_expression'
        MODULE_COEXPRESSION_NETWORK = 'module_coexpression_network'

        PLOT_NAMES = {
            'distribution': [
                (SAMPLE_SETS_MAGNITUDE_DISTRIBUTION, Score.RankMethods.MAGNITUDE),
                (SAMPLE_SETS_COEXPRESSION_DISTRIBUTION, Score.RankMethods.COEXPRESSION),
                (BIOFEATURES_UNCENTERED_CORRELATION_DISTRIBUTION, Score.RankMethods.UNCENTERED_CORRELATION)
            ],
            'heatmap': [
                MODULE_HEATMAP_EXPRESSION
            ],
            'network': [
                MODULE_COEXPRESSION_NETWORK
            ]
        }

        @staticmethod
        def get_plot_names():
            return Plot.PlotType.PLOT_NAMES

    def get_plot(self, type, **kwargs):
        rank_name = None
        for rn in Plot.PlotType.PLOT_NAMES['distribution']:
            if rn[0] == type:
                rank_name = rn[1]
                break
        if type == Plot.PlotType.SAMPLE_SETS_MAGNITUDE_DISTRIBUTION:
            return self._plot_sample_sets_magnitude_distribution(rank_name)
        elif type == Plot.PlotType.SAMPLE_SETS_COEXPRESSION_DISTRIBUTION:
            return self._plot_sample_sets_coexpression_distribution(rank_name)
        elif type == Plot.PlotType.BIOFEATURES_UNCENTERED_CORRELATION_DISTRIBUTION:
            return self._plot_biofeatures_centered_correlation_distribution(rank_name)
        elif type == Plot.PlotType.MODULE_HEATMAP_EXPRESSION:
            sort_by = kwargs.get('sort_by', 'expression')
            alternative_coloring = bool(kwargs.get('alternative_coloring', False))
            min = kwargs.get('min', None)
            max = kwargs.get('max', None)
            return self._plot_module_heatmap(sort_by=sort_by, alternative_coloring=alternative_coloring, min=min, max=max)
        elif type == Plot.PlotType.MODULE_COEXPRESSION_NETWORK:
            return self._plot_module_coexpression_network(**kwargs)

    def _plot_module_coexpression_network(self, **kwargs):
        corr_threshold = kwargs.get('threshold', 0.7)
        sign = kwargs.get('sign', 'both')
        layout = kwargs.get('layout', 'kamada_kawai')

        g = nx.Graph()
        g.add_nodes_from(self.get_biological_feature_names())
        corr = np.array(pd.DataFrame(self.normalized_values).T.corr())

        nodes = list(g.nodes)
        for i in range(len(nodes)):
            for j in range(i, len(nodes)):
                if i != j and sign == 'both' and np.abs(corr[i][j]) >= corr_threshold:
                    g.add_edge(nodes[i], nodes[j], corr=corr[i][j])
                elif i != j and sign == 'positive' and corr[i][j] >= corr_threshold:
                    g.add_edge(nodes[i], nodes[j], corr=corr[i][j])
                elif i != j and sign == 'negative' and corr[i][j] <= (-1 * corr_threshold):
                    g.add_edge(nodes[i], nodes[j], corr=corr[i][j])

        if layout == 'kamada_kawai':
            pos = nx.kamada_kawai_layout(g)
        elif layout == 'fruchterman_reingold':
            pos = nx.fruchterman_reingold_layout(g)
        elif layout == 'circular':
            pos = nx.circular_layout(g)
        elif layout == 'shell':
            pos = nx.shell_layout(g)
        elif layout == 'spectral':
            pos = nx.spectral_layout(g)
        elif layout == 'spring':
            pos = nx.spring_layout(g)

        edge_traces = []

        for edge in g.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            corr = g.edges[edge]['corr']
            width = 5 ** np.abs(corr)
            color = 'purple'
            if corr < 0:
                color = 'orange'

            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                line=dict(width=width, color=color),
                hoverinfo='none',
                mode='lines',
                )
            edge_traces.append(edge_trace)

        node_trace = go.Scatter(
            x=[],
            y=[],
            text=[],
            mode='markers',
            hoverinfo='text',
            marker=dict(
                showscale=False,
                reversescale=False,
                color='gray',
                size=15,
                line=dict(width=2)))

        for node in g.nodes():
            x, y = pos[node]
            node_trace['x'] += tuple([x])
            node_trace['y'] += tuple([y])

        for node, adjacencies in enumerate(g.adjacency()):
            node_info = adjacencies[0]
            node_trace['text'] += tuple([node_info])

        fig = go.Figure(data=edge_traces + [node_trace],
                 layout=go.Layout(
                    title='Module coexpression network<br>'
                          'Pearson correlation threshold: ' + str(corr_threshold),
                    titlefont=dict(size=16),
                    showlegend=False,
                    hovermode='closest',
                    margin=dict(b=20,l=5,r=5,t=40),
                    xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                    yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)))

        return fig

    def _plot_module_heatmap(self, sort_by='expression', alternative_coloring=False, min=None, max=None):
        colorscale = [
            [0.0, 'rgb(0, 255, 0)'],
            [0.15, 'rgb(0, 255, 0)'],
            [0.5, 'rgb(0, 0, 0)'],
            [0.85, 'rgb(255, 0, 0)'],
            [1.0, 'rgb(255, 0, 0)'],
        ]
        alternative_colorscale = [
                [0, 'rgb(255, 255, 0)'],
                [0.15, 'rgb(255, 255, 0)'],
                [0.5, 'rgb(0, 0, 0)'],
                [0.85, 'rgb(0, 255, 255)'],
                [1, 'rgb(0, 255, 255)'],
            ]
        if alternative_coloring:
            colorscale = alternative_colorscale

        min = min if min else self.min
        max = max if max else self.max
        cluster = Cluster(self.normalized_values, max=max, min=min)
        _data, cg, cc, g, c = cluster.get_cluster(method=sort_by)

        d = np.array(_data)
        d = np.isnan(d).astype(int)

        bf_ids = self.get_biological_feature_ids()
        ss_ids = self.get_sample_set_ids()
        bf_names = self.get_biological_feature_names()
        ss_names = self.get_sample_set_names()
        exp_names = self.get_experiments_access_id()
        plt_names = self.get_platforms_access_id()

        hovertext = list()
        for yi, yy in enumerate(g):
            hovertext.append(list())
            for xi, xx in enumerate(c):
                hovertext[-1].append('Sample set: {}<br /> ' \
                                     'Bio feature: {}<br /> ' \
                                     'Value: {} <br />' \
                                     'Experiments: {} <br />' \
                                     'Platformss: {}'.format(ss_names[xx], bf_names[yy], _data[yi][xi], exp_names[xx], plt_names[xx]))

        cell_ratio = _data.shape[0] / _data.shape[1]

        line_color = 'rgb(255, 255, 255)'
        line_width = 1.5
        cluster_lines_h = []
        cluster_lines_v = []
        g_unique, g_counts = np.unique(cg, return_counts=True)
        current = -0.5
        for g_count in g_counts:
            current += g_count
            cluster_lines_h.append(
                {
                    'type': 'line',
                    'x0': -1,
                    'y0': current,
                    'x1': _data.shape[1],
                    'y1': current,
                    'line': {
                        'color': line_color,
                        'width': line_width,
                    },
                }
            )
        c_unique, c_counts = np.unique(cc, return_counts=True)
        current = -0.5
        for c_count in c_counts:
            current += c_count
            cluster_lines_v.append(
                {
                    'type': 'line',
                    'x0': current,
                    'y0': -1,
                    'x1': current,
                    'y1': _data.shape[0],
                    'line': {
                        'color': line_color,
                        'width': line_width,
                    },
                }
            )

        trace = go.Heatmap(
                z=_data,
                x=[to_global_id('SampleSetType', ss_ids[i]) for i in c],
                y=[to_global_id('BioFeatureType', bf_ids[i]) for i in g],
                colorscale=colorscale,
                showlegend=False,
                hoverinfo='text',
                text=hovertext,
                showscale=True,
                zmax=cluster.max,
                zmin=cluster.min
            )

        nantrace = go.Heatmap(
                z=d,
                colorscale=[
                    [0, 'rgb(0, 0, 0)'],
                    [1, 'rgb(100, 100, 100)'],
                ],
                showscale=False,
                hoverinfo='skip'
            )

        layout = go.Layout(
            title='Heatmap',
            shapes=cluster_lines_h + cluster_lines_v,
            xaxis=dict(
                title='Sample Sets',
                range=[0, _data.shape[1]],
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks='',
                showticklabels=False,
                autorange=True,
            ),
            yaxis=dict(
                title='Biological Features',
                range=[0, _data.shape[0] * (2 + (1 - cell_ratio))],
                showgrid=False,
                zeroline=False,
                showline=False,
                ticks='',
                showticklabels=False,
                autorange=True,
            )
        )

        fig = go.Figure(data=[nantrace, trace], layout=layout)
        return fig, g, c, g_counts, c_counts

    def _plot_biofeatures_centered_correlation_distribution(self, rank_name):
        norm_basename = None
        for n in self.db['normalizations']:
            if n['name'] == self.normalization_name:
                norm_basename = n['normalized_file_basename']
                break
        if not norm_basename:
            raise Exception('Cannot find normalized values')
        cnv = CompiledNormalizedData(n['normalized_file_basename'])
        values = cnv.df[list(self.sample_sets)]

        score = Score(values, self.biological_features, self.sample_sets)
        rank = score.rank_biological_features(rank_name)
        rank = rank.replace([np.inf, -np.inf], np.nan)

        x = sorted(rank.dropna().values)
        y = list(range(len(x)))[::-1]

        trace = go.Scatter(
            x=x,
            y=y,
            name=''
        )

        _fig = ff.create_distplot([rank.dropna().values], [''], show_hist=False)

        fig = tools.make_subplots(rows=2, cols=1)
        fig.append_trace(_fig.data[0], 2, 1)
        fig.append_trace(trace, 1, 1)
        fig['layout'].update(title='Uncentered correlation',
                             xaxis1=dict(title='cutoff',
                                         autorange=True
                                         ),
                             yaxis1=dict(title='#selected biological features'),
                             xaxis2=dict(title='uncentered correlation',
                                         autorange=True
                                         ),
                             yaxis2=dict(title='relative frequency')
                             )
        fig.layout.showlegend = False

        df = pd.DataFrame(rank)
        df['gid'] = [to_global_id('BioFeatureType', i) for i in df.index]
        _names_dict = dict(BioFeature.objects.using(self.db['name']).filter(id__in=[i for i in df.index]).values_list('id', 'name'))
        df['name'] = [_names_dict[i] for i in df.index]
        df['type'] = ['BioFeatureType' for i in df.index]
        df = df.set_index('gid')
        df.columns = ['value', 'name', 'type']

        return fig, df

    def _plot_sample_sets_coexpression_distribution(self, rank_name):
        norm_basename = None
        for n in self.db['normalizations']:
            if n['name'] == self.normalization_name:
                norm_basename = n['normalized_file_basename']
                break
        if not norm_basename:
            raise Exception('Cannot find normalized values')
        cnv = CompiledNormalizedData(n['normalized_file_basename'])
        values = cnv.df.loc[list(self.biological_features)]

        score = Score(values, self.biological_features, self.sample_sets)
        rank = score.rank_sample_sets(rank_name)
        rank = rank.replace([np.inf, -np.inf], np.nan)

        x = sorted(rank.replace([np.inf, -np.inf], np.nan).dropna().values)
        y = list(range(len(x)))[::-1]

        trace = go.Scatter(
            x=x,
            y=y,
            name=''
        )

        _fig = ff.create_distplot([rank.replace([np.inf, -np.inf], np.nan).dropna().values], [''], show_hist=False)

        fig = tools.make_subplots(rows=2, cols=1)
        fig.append_trace(_fig.data[0], 2, 1)
        fig.append_trace(trace, 1, 1)
        fig['layout'].update(title='Coexpression behavior',
                             xaxis1=dict(title='cutoff',
                                         rangemode='nonnegative',
                                         autorange=True
                                         ),
                             yaxis1=dict(title='#selected sample sets'),
                             xaxis2=dict(title='inverse coefficient of variation, threshold average',
                                         rangemode='nonnegative',
                                         autorange=True
                                         ),
                             yaxis2=dict(title='relative frequency')
                             )
        fig.layout.showlegend = False

        df = pd.DataFrame(rank)
        df['gid'] = [to_global_id('SampleSetType', i) for i in df.index]
        _names_dict = dict(NormalizationDesignGroup.objects.using(self.db['name']).filter(id__in=[i for i in df.index]).values_list('id','name'))
        df['name'] = [_names_dict[i] for i in df.index]
        df['type'] = ['SampleSetType' for i in df.index]
        df = df.set_index('gid')
        df.columns = ['value', 'name', 'type']

        return fig, df

    def _plot_sample_sets_magnitude_distribution(self, rank_name):
        norm_basename = None
        for n in self.db['normalizations']:
            if n['name'] == self.normalization_name:
                norm_basename = n['normalized_file_basename']
                break
        if not norm_basename:
            raise Exception('Cannot find normalized values')
        cnv = CompiledNormalizedData(n['normalized_file_basename'])
        values = cnv.df.loc[list(self.biological_features)].values

        score = Score(values, self.biological_features, self.sample_sets)
        rank = score.rank_sample_sets(rank_name)
        rank = rank.replace([np.inf, -np.inf], np.nan)

        x = sorted(rank.dropna().values)
        y = list(range(len(x)))[::-1]

        trace = go.Scatter(
            x=x,
            y=y,
            name=''
        )

        _fig = ff.create_distplot([rank.dropna().values], [''], show_hist=False)

        fig = tools.make_subplots(rows=2, cols=1)
        fig.append_trace(_fig.data[0], 2, 1)
        fig.append_trace(trace, 1, 1)
        fig['layout'].update(title='Magnitude of expression changes',
                             xaxis1=dict(title='cutoff'),
                             yaxis1=dict(title='#selected sample sets'),
                             xaxis2=dict(title='abs(M) value cutoff'),
                             yaxis2=dict(title='relative frequency')
                             )
        fig.layout.showlegend = False

        df = pd.DataFrame(rank)
        df['gid'] = [to_global_id('SampleSetType', i) for i in df.index]
        _names_dict = dict(NormalizationDesignGroup.objects.using(self.db['name']).filter(id__in=[i for i in df.index]).values_list('id','name'))
        df['name'] = [_names_dict[i] for i in df.index]
        df['type'] = ['SampleSetType' for i in df.index]
        df = df.set_index('gid')
        df.columns = ['value', 'name', 'type']

        return fig, df
