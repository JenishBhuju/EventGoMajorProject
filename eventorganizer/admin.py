from django.contrib import admin
from .models import Event, Category, EventCategory,Preference,UserPreference

admin.site.register(Event)
admin.site.register(Category)
admin.site.register(EventCategory)
admin.site.register(Preference)
admin.site.register(UserPreference)