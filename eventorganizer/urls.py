from django.urls import path
from . import views

urlpatterns = [
    path('create/', views.create_event, name='create-event'),
    path('update/<int:event_id>/', views.update_event, name='update-event'),
    path('detail/<int:event_id>/', views.event_detail, name='event-detail'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete-event'),
    path('search/', views.event_search, name='event-search'),
    path('messages/', views.view_messages, name='view-messages'),
    path('map/', views.map_show, name='map-show'),
    path('nearest/', views.nearest, name='nearest'),
]
