import graphene

import compass_graphql.lib.schema.data_source
import compass_graphql.lib.schema.experiment
import compass_graphql.lib.schema.platform
import compass_graphql.lib.schema.platform_type
import compass_graphql.lib.schema.bio_feature
import compass_graphql.lib.schema.sample
import compass_graphql.lib.schema.module
import compass_graphql.lib.schema.biofeature_annotation
import compass_graphql.lib.schema.compendium
import compass_graphql.lib.schema.sample_annotation
import compass_graphql.lib.schema.ontology
import compass_graphql.lib.schema.ontology_node
import compass_graphql.lib.schema.sample_set
import compass_graphql.lib.schema.normalization
import compass_graphql.lib.schema.score_rank_methods
import compass_graphql.lib.schema.plot
import compass_graphql.lib.schema.annotation_pretty_print
import compass_graphql.lib.schema.version
import compass_graphql.lib.schema.sparql


class Query(compass_graphql.lib.schema.data_source.Query,
            compass_graphql.lib.schema.experiment.Query,
            compass_graphql.lib.schema.platform.Query,
            compass_graphql.lib.schema.platform_type.Query,
            compass_graphql.lib.schema.bio_feature.Query,
            compass_graphql.lib.schema.sample.Query,
            compass_graphql.lib.schema.module.Query,
            compass_graphql.lib.schema.biofeature_annotation.Query,
            compass_graphql.lib.schema.compendium.Query,
            compass_graphql.lib.schema.sample_annotation.Query,
            compass_graphql.lib.schema.ontology.Query,
            compass_graphql.lib.schema.ontology_node.Query,
            compass_graphql.lib.schema.sample_set.Query,
            compass_graphql.lib.schema.normalization.Query,
            compass_graphql.lib.schema.score_rank_methods.Query,
            compass_graphql.lib.schema.plot.Query,
            compass_graphql.lib.schema.annotation_pretty_print.Query,
            compass_graphql.lib.schema.version.Query,
            compass_graphql.lib.schema.sparql.Query,
            graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass

schema = graphene.Schema(query=Query)
