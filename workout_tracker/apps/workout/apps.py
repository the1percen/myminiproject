from django.apps import AppConfig

class WorkoutConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.workout'   # full path to app
    label = 'workout'       # short label Django uses internally

