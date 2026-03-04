"""workout_tracker URL Configuration

Points our project to our workout application.
"""
from django.urls import path, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.workout.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
