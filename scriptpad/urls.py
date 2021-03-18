
from django.urls import path,include
from django.views.generic import TemplateView

from django.conf.urls import url
from rest_framework.routers import DefaultRouter
from scriptpad import views


router = DefaultRouter()
router.register(r'vp', views.Vp)

urlpatterns = [
    path('',TemplateView.as_view(template_name="index.html")),
    path('api/task/', views.Task.as_view()),
    path('api/Taskatmobilesoption/', views.Taskatmobilesoption.as_view()),
    path('api/tablesearch/', views.TableSearch.as_view()),
    path('api/tablepreview/', views.TablePreview.as_view()),
    path('api/history/', views.TaskHistoryviewset.as_view({'get': 'list'})),
    path('api/crontab/', views.crontab.as_view()),
    url('api/crontab/(?P<pk>[0-9]+)/$', views.crontab.as_view()),

    path('api/serverscript/', views.serverScript.as_view()),
    path('api/serverscript/<str:filename>/', views.serverScript.as_view()),
    path('api/killtask/<int:taskid>/<str:listname>/', views.killtask),
    path(r'api/', include(router.urls)),
]