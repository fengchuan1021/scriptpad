"""scriptpad URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
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
from django.contrib import admin
from django.urls import path,include
from django.conf.urls import url
from django.views.generic import TemplateView
from rest_framework.routers import DefaultRouter
from task import views
from task import serverscriptview as sview
router = DefaultRouter()
router.register(r'vp', views.Vp)

urlpatterns = [
    path('',TemplateView.as_view(template_name='index.html')),
    path('api/task/', views.Task.as_view()),
    path('api/Taskatmobilesoption/',views.Taskatmobilesoption.as_view()),
    path('api/tablesearch/', views.TableSearch.as_view()),
    path('api/tablepreview/', views.TablePreview.as_view()),
    path('api/history/', views.TaskHistoryviewset.as_view({'get': 'list'})),
    path('api/crontab/',views.crontab.as_view()),
    url('api/crontab/(?P<pk>[0-9]+)/$',views.crontab.as_view()),

    path('api/serverscript/', sview.serverScript.as_view()),
    path('api/serverscript/<str:filename>/', sview.serverScript.as_view()),
    path('api/killtask/<int:taskid>/<str:listname>/',views.killtask),
    path('api/executecommand/<path:command>',views.executecommand),
    path(r'api/', include(router.urls)),
   # path('api/remotescript/', views.RemoteScript.as_view({'get': 'list'})),
    #path('api/vp/', views.Vp.as_view({'get': 'list','post':'create'})),
]
