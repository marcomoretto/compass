import json
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.conf import settings
import os

import graphene
from graphene import ObjectType
from graphene.types.resolver import dict_resolver
from graphql_relay import from_global_id

from compass_graphql.lib.utils.compendium_config import CompendiumConfig
from compass_graphql.lib.utils.plot import Plot
from compass_graphql.lib.utils.module import get_normalization_name_from_sample_set_id, InitModuleProxy

from plotly.offline import download_plotlyjs, init_notebook_mode, plot, iplot
import plotly.io
import importlib


class PlotNameType(ObjectType):

    class Meta:
        default_resolver = dict_resolver

    distribution = graphene.List(graphene.String)
    heatmap = graphene.List(graphene.String)
    network = graphene.List(graphene.String)


class PlotType(ObjectType):
    json = graphene.String()
    html = graphene.String()

    def resolve_json(self, info, **kwargs):
        return plotly.io.to_json(self[0])

    def resolve_html(self, info, **kwargs):
        plt = self[0]
        plot_type = self[1]
        js = ''
        div = plot(plt, include_plotlyjs=False, output_type='div')
        plotly = '<script>{src}</script>'.format(src=open(settings.BASE_DIR +  static('compass/js/plotly/plotly-latest.min.js'), 'r').read())
        if plot_type == Plot.PlotType.MODULE_COEXPRESSION_NETWORK:
            div = plotly + div + js
        else:
            if plot_type == Plot.PlotType.MODULE_HEATMAP_EXPRESSION:
                id = div.split('=')[1].split()[0].replace("'", "").replace('"', '')
                js = '''
                    <script>
                    var myDiv = document.getElementById('{div_id}');
                    myDiv.on('plotly_relayout',
                        function(eventdata) {{
                            console.log(myDiv.id);
                            var xRange = [eventdata['xaxis.range[0]'], eventdata['xaxis.range[1]']]
                            var yRange = [eventdata['yaxis.range[0]'], eventdata['yaxis.range[1]']]
                            var calcdata = myDiv.calcdata[1][0]
                            var xInside = []
                            var yInside = []
                
                            for (var i = 0; i < calcdata.trace.y.length; i++) {{
                                var y = calcdata.y[i]
                                if(y > yRange[0] && y < yRange[1]) {{
                                    yInside.push(calcdata.trace.y[i])
                                }}
                            }}
                            for (var i = 0; i < calcdata.trace.x.length; i++) {{
                                var x = calcdata.x[i]
                                if(x > xRange[0] && x < xRange[1]) {{
                                    xInside.push(calcdata.trace.x[i])
                                }}
                            }}
                            console.log(
                                JSON.stringify({{'sample_sets': xInside, 'biological_features': yInside}})
                            )
                        }}
                    );
                    </script>'''.format(div_id=id)
            div = plotly + div + js
        return div


class Query(object):
    plot_name = graphene.Field(PlotNameType,
                               compendium=graphene.String(required=True),
                               normalization=graphene.String(required=True))

    plot_distribution = graphene.Field(PlotType,
                                        compendium=graphene.String(required=True),
                                        plot_type=graphene.String(required=True),
                                        normalization=graphene.String(),
                                        name=graphene.String(),
                                        biofeatures_ids=graphene.List(of_type=graphene.ID),
                                        sampleset_ids=graphene.List(of_type=graphene.ID))

    plot_heatmap = graphene.Field(PlotType,
                                    compendium=graphene.String(required=True),
                                    plot_type=graphene.String(required=True),
                                    name=graphene.String(),
                                    sort_by=graphene.String(),
                                    alternative_coloring=graphene.Boolean(),
                                    biofeatures_ids=graphene.List(of_type=graphene.ID),
                                    sampleset_ids=graphene.List(of_type=graphene.ID))

    plot_network = graphene.Field(PlotType,
                                  compendium=graphene.String(required=True),
                                  plot_type=graphene.String(required=True),
                                  name=graphene.String(),
                                  biofeatures_ids=graphene.List(of_type=graphene.ID),
                                  sampleset_ids=graphene.List(of_type=graphene.ID),
                                  threshold=graphene.Float(),
                                  sign=graphene.String(),
                                  layout=graphene.String())

    def resolve_plot_name(self, info, compendium, normalization, **kwargs):
        conf = CompendiumConfig(compendium)
        plot_class = conf.get_plot_class(normalization)
        _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
        _class = plot_class.split('.')[-1]
        _plot_class = getattr(_module, _class)
        return _plot_class.PlotType.get_plot_names()

    def resolve_plot_network(self, info, compendium, plot_type, **kwargs):
        conf = CompendiumConfig(compendium)
        normalization = get_normalization_name_from_sample_set_id(compendium, from_global_id(kwargs["sampleset_ids"][0])[1])
        plot_class = conf.get_plot_class(normalization)
        _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
        _class = plot_class.split('.')[-1]
        _plot_class = getattr(_module, _class)
        module_proxy_class = InitModuleProxy(_plot_class)
        m = module_proxy_class(compendium, info.context.user, normalization=normalization)
        m.set_global_biofeatures(kwargs["biofeatures_ids"])
        m.set_global_samplesets(kwargs["sampleset_ids"])
        m.get_normalized_values()

        return m.get_plot(plot_type, **kwargs), plot_type

    def resolve_plot_heatmap(self, info, compendium, plot_type, **kwargs):
        conf = CompendiumConfig(compendium)
        normalization = get_normalization_name_from_sample_set_id(compendium, from_global_id(kwargs["sampleset_ids"][0])[1])
        plot_class = conf.get_plot_class(normalization)
        _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
        _class = plot_class.split('.')[-1]
        _plot_class = getattr(_module, _class)
        module_proxy_class = InitModuleProxy(_plot_class)
        m = module_proxy_class(compendium, info.context.user, normalization=normalization)
        m.set_global_biofeatures(kwargs["biofeatures_ids"])
        m.set_global_samplesets(kwargs["sampleset_ids"])
        m.get_normalized_values()

        sort_by = kwargs.get('sort_by', 'expression')
        alternative_coloring = bool(kwargs.get('alternative_coloring', False))

        return m.get_plot(plot_type, sort_by=sort_by, alternative_coloring=alternative_coloring), plot_type

    def resolve_plot_distribution(self, info, compendium, plot_type, **kwargs):
        normalization = kwargs['normalization'] if 'normalization' in kwargs else None

        conf = CompendiumConfig(compendium)
        plot_class = conf.get_plot_class(normalization)
        _module = importlib.import_module('.'.join(plot_class.split('.')[:-1]))
        _class = plot_class.split('.')[-1]
        _plot_class = getattr(_module, _class)
        module_proxy_class = InitModuleProxy(_plot_class)

        m = module_proxy_class(compendium, info.context.user, normalization=normalization)
        if "biofeatures_ids" in kwargs:
            m.set_global_biofeatures(kwargs["biofeatures_ids"])
        if "sampleset_ids" in kwargs:
            m.set_global_samplesets(kwargs["sampleset_ids"])

        return m.get_plot(plot_type), plot_type
