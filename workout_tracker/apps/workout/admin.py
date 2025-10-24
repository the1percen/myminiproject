from django.contrib import admin
from .models import User, Workout, Exercise


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email', 'level_name', 'created_at')
    search_fields = ('username', 'email')
    list_filter = ('level_name', 'created_at')
    ordering = ('-created_at',)


@admin.register(Workout)
class WorkoutAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'user', 'completed', 'created_at')
    search_fields = ('name', 'description')
    list_filter = ('completed', 'created_at')
    ordering = ('-created_at',)


@admin.register(Exercise)
class ExerciseAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'weight', 'repetitions', 'category', 'workout', 'created_at')
    search_fields = ('name', 'category')
    list_filter = ('category', 'created_at')
    ordering = ('-created_at',)
