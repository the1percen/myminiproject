"""workout_tracker URL Configuration

Points our project to our workout application.
"""
from django.urls import path, include
from django.contrib import admin

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.workout.urls')),
]
