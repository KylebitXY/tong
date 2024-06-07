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
    

@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ('name', 'passport_photo', 'gender', 'id_passport_number', 'role', 'contacts')
    search_fields = ('name', 'id_passport_number', 'role')
    list_filter = ('role', 'gender')
    
@admin.register(Media)
class MediaAdmin(admin.ModelAdmin):
    list_display = ('name', 'passport_photo', 'id_passport_number', 'role', 'contacts', 'media_house')
    search_fields = ('name', 'id_passport_number', 'role', 'media_house')
    list_filter = ('role', 'gender')


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ('name', 'joined_date')
    search_fields = ('name',)


@admin.register(Belt)
class BeltAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
    
    
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',) 
    
@admin.register(RoleType)
class RoleTypeAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)    
 
 @admin.register(Club)
class ClubAdmin(admin.ModelAdmin):
    list_display = ('name', 'county', 'joined_date')
    search_fields = ('name', 'county')
    list_filter = ('county',)      