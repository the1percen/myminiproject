"""workout app URL Configuration

Our workout application URLs.
"""
from django.urls import path, re_path
from . import views

urlpatterns = [
    path('', views.login, name='login'),  # index / login page
    path('user/register/', views.register, name='register'),  # register page
    path('user/login/', views.login, name='user_login'),  # login user
    path('user/logout/', views.logout, name='logout'),  # logout
    path('dashboard/', views.dashboard, name='dashboard'),  # dashboard
    path('workout/', views.new_workout, name='new_workout'),  # new workout page
    re_path(r'^workout/(?P<id>\d+)/$', views.workout, name='workout'),  # get/update workout
    re_path(r'^workout/(?P<id>\d+)/exercise/$', views.exercise, name='exercise'),  # add exercise
    re_path(r'^workout/(?P<id>\d+)/complete/$', views.complete_workout, name='complete_workout'),  # complete workout
    re_path(r'^workout/(?P<id>\d+)/edit/$', views.edit_workout, name='edit_workout'),  # edit workout
    re_path(r'^workout/(?P<id>\d+)/delete/$', views.delete_workout, name='delete_workout'),  # delete workout
    path('workouts/', views.all_workouts, name='all_workouts'),  # all workouts
    path('legal/tos/', views.tos, name='tos'),  # terms of service
    path('chatbot/', views.chatbot, name='chatbot'),  # chatbot page
]
