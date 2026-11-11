from django.urls import path
from . import views

urlpatterns = [
    path('time', views.time_view, name='time'),
    path('sum', views.sum_view, name='sum'),
    path('', views.index, name='home'),
    path('index.html', views.index, name='index_html'),
    path("new", views.new, name="new"),
    path("createUser", views.createUser, name="createUser"),
    path("createCourse", views.createCourse, name="createCourse"),
    path("createLecture", views.createLecture, name="createLecture"),
    path("createQRCodeUpload", views.createQRCodeUpload, name="createQRCodeUpload"),
    path("dumpUploads", views.dumpUploads, name="dumpUploads"),
]

