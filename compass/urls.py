"""compass URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf.urls import url, include
from graphene_django.views import GraphQLView

from compass_graphql import views
from compass_graphql.schema import schema

class COMPASSGraphQLView(GraphQLView):
    graphiql_template = 'compass_graphql/graphiql.html'


graphql_view = COMPASSGraphQLView.as_view(graphiql=True, schema=schema)

urlpatterns = [
    url(r'^$', views.home, name='home'),
    url(r'^graphql', graphql_view),
    url(r'^vespucci', views.vespucci, name='vespucci'),
]
