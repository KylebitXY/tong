from django.contrib import admin
from .models import (
    Athlete, Coach, Staff, Media, Country, Belt, Category, RoleType, Club, Accommodation, Team, Membership
)

@admin.register(Athlete)
class AthleteAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'passport_photo',
        'country',
        'region',
        'dob',
        'weight',
        'get_categories',
        'belt',
        'coach',
    )

    search_fields = (
        'name',
        'passport',
        'region__name',
        'region__county',
        'country__name',
    )

    list_filter = (
        'country',
        'category',
        'region',
        'belt',
        'coach',
    )

    autocomplete_fields = ('country', 'region', 'coach')

    def get_categories(self, obj):
        return ", ".join(category.get_name_display() for category in obj.category.all())

    get_categories.short_description = 'Categories'

@admin.register(Coach)
class CoachAdmin(admin.ModelAdmin):
    list_display = ('name', 'passport_photo', 'country', 'region', 'dob', 'level', 'belt', 'is_athlete','get_categories')
    search_fields = ('name', 'passport', 'country__name')
    list_filter = ('country', 'level', 'belt')
    def get_categories(self, obj):
        # Access the many-to-many field correctly
        return ", ".join([category.name for category in obj.category.all()])
    get_categories.short_description = 'Categories'
    

    
