from django.urls import path

from . import views
urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('events/', views.event_list, name='event-list'),
    path('save-preferences/', views.save_user_preferences, name='save_preferences'),
    path('update-preferences/', views.update_preferences, name='update-preferences'),
    path('dashboard/', views.dashboard, name='dashboard'),
]
