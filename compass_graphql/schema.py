import graphene
import graphql_jwt

import compass_graphql.lib.schema.data_source
import compass_graphql.lib.schema.experiment
import compass_graphql.lib.schema.platform
import compass_graphql.lib.schema.platform_type
import compass_graphql.lib.schema.bio_feature
import compass_graphql.lib.schema.sample
import compass_graphql.lib.schema.manage_module
import compass_graphql.lib.schema.module
import compass_graphql.lib.schema.biofeature_annotation
import compass_graphql.lib.schema.annotation_value
import compass_graphql.lib.schema.compendium
import compass_graphql.lib.schema.sample_annotation
import compass_graphql.lib.schema.ontology
import compass_graphql.lib.schema.ontology_node
import compass_graphql.lib.schema.sample_set
import compass_graphql.lib.schema.normalization
import compass_graphql.lib.schema.score_rank_methods
import compass_graphql.lib.schema.plot
import compass_graphql.lib.schema.signup


class Query(compass_graphql.lib.schema.data_source.Query,
            compass_graphql.lib.schema.experiment.Query,
            compass_graphql.lib.schema.platform.Query,
            compass_graphql.lib.schema.platform_type.Query,
            compass_graphql.lib.schema.bio_feature.Query,
            compass_graphql.lib.schema.sample.Query,
            compass_graphql.lib.schema.manage_module.Query,
            compass_graphql.lib.schema.module.Query,
            compass_graphql.lib.schema.biofeature_annotation.Query,
            compass_graphql.lib.schema.annotation_value.Query,
            compass_graphql.lib.schema.compendium.Query,
            compass_graphql.lib.schema.sample_annotation.Query,
            compass_graphql.lib.schema.ontology.Query,
            compass_graphql.lib.schema.ontology_node.Query,
            compass_graphql.lib.schema.sample_set.Query,
            compass_graphql.lib.schema.normalization.Query,
            compass_graphql.lib.schema.score_rank_methods.Query,
            compass_graphql.lib.schema.plot.Query,
            graphene.ObjectType):
    # This class will inherit from multiple Queries
    # as we begin to add more apps to our project
    pass


class CompassMutations(graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

    signup = compass_graphql.lib.schema.signup.Signup.Field()
    save_module = compass_graphql.lib.schema.manage_module.SaveModule.Field()
    update_module_name = compass_graphql.lib.schema.manage_module.UpdateModuleName.Field()
    delete_module = compass_graphql.lib.schema.manage_module.DeleteModule.Field()


schema = graphene.Schema(query=Query, mutation=CompassMutations)