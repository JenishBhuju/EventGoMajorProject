import asyncio
from datetime import date
from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Message, UserPreference
from authuser.models import CustomUser
from .models import Category, Event,Preference
from .forms import EventForm,UserPreferenceForm
from django.contrib.auth.decorators import login_required  
from django.shortcuts import render, redirect, get_object_or_404
# import paho.mqtt.publish as publish
import folium
from folium import GeoJson
from geopy.distance import geodesic
import numpy as np
import json
from django.core.cache import cache
from django.contrib import messages
from django.db.models import Q

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.user_id = request.user
            event.save()
            form._save_categories(event)

            normal_users = CustomUser.objects.filter(user_type='normal')

            for user in normal_users:
                user_preferences = UserPreference.objects.filter(user_id=user)
                user_category_names = [preference.preference_id.name for preference in user_preferences]

                events_sent_key = f"events_sent_{user.username}"
                events_sent = cache.get(events_sent_key, set())

                # for event in Event.objects.exclude(id__in=events_sent):
                #     event_category_names = event.categories.values_list('name', flat=True)
                #     if any(category_name in user_category_names for category_name in event_category_names):
                #         message_content = f"New event created: {event.title}"
                #         message = Message.objects.create(sender=request.user, recipient=user, event=event, content=message_content)
                #         publish.single(f"events/{user.username}", payload=message_content, hostname="localhost")
                #         events_sent.add(event.id)  # Mark event as sent

                cache.set(events_sent_key, events_sent)

            messages.success(request, 'Event created successfully!')
            request.session['event_created'] = True  # Set event_created in the session
            return redirect('event-list')  
    else:
        form = EventForm()

    return render(request, 'organizer/create_event.html', {'form': form})

@login_required
def update_event(request, event_id):
    event = Event.objects.get(pk=event_id)
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES, instance=event)
        if form.is_valid():
            event = form.save(commit=False)
            event.user_id = request.user
            event.save()
            form._save_categories(event)

            messages.success(request, 'Event updated successfully!')
            request.session['event_updated'] = True 
            return redirect('event-list') 
            
    else:
        form = EventForm(instance=event)
    
    return render(request, 'organizer/update_event.html', {'form': form, 'event': event})

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    if request.user != event.user_id:  # Ensure the user can only delete their own events
        return JsonResponse({'error': 'You do not have permission to delete this event.'}, status=403)
    event.delete()
    messages.success(request, 'Event deleted successfully!')
    request.session['event_deleted'] = True  
    return redirect('event-list')  

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    is_organizer = request.user.is_organizer
    event_coordinate = [event.latitude, event.longitude]
    location_map = folium.Map(location=event_coordinate, zoom_start=13, tiles='OpenStreetMap', control_scale=True)
    location_map.get_root().html.add_child(folium.Element())
    folium.Marker(location=event_coordinate, popup=folium.Popup(f"{event.title} : {event.description}", parse_html=True, show=True, permanent=True)).add_to(location_map)
    map_html = location_map._repr_html_()
    return render(request, 'organizer/event_detail.html', {'event': event, 'is_organizer': is_organizer, 'map_html': map_html})

@login_required
def event_search(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    # Get all events
    current_date = date.today()
    events = Event.objects.filter(date__gte=current_date)

    # Apply filters if provided
    if query:
        events = events.filter(Q(title__icontains=query) | Q(description__icontains=query))

    if category:
        events = events.filter(categories__name=category)

    # Get all categories
    categories = Category.objects.all()

    return render(request, 'normal/event_search.html', {'events': events, 'categories': categories})

def view_messages(request):
    # Retrieve messages for the current user (assuming the user is normal)
    messages = Message.objects.filter(recipient=request.user)
    return render(request, 'normal/messages.html', {'messages': messages})

def map_show(request):
    current_date = date.today() 
    if request.method == 'POST':
        place_name = request.POST.get('place_name')

        if place_name == None:
            location = [28.150875468598606, 84.462890625]
            location_map = folium.Map(location=location, zoom_start=8, tiles='OpenStreetMap', control_scale=True)
            location_map.get_root().html.add_child(folium.Element('<style>.leaflet-container { filter: hue-rotate(100deg) brightness(90%) saturate(100%); }</style>'))
            locations = Event.objects.filter(date__gte=current_date)
            for i in locations:
                title = i.title
                latitude = i.latitude
                longitude = i.longitude
                location_coords = [latitude, longitude]
                folium.Marker(location=location_coords, popup=folium.Popup(f"{title}", parse_html=True, show=True, permanent=True)).add_to(location_map)
            
            try:
                latitude = request.POST.get('latitude')
                longitude = request.POST.get('longitude')
                place_location = [latitude, longitude]
                folium.Marker(location=place_location, popup=folium.Popup("You", parse_html=True, show=True, permanent=True), icon=folium.Icon(color='red')).add_to(location_map)
            except:
                pass

            map_html = location_map._repr_html_()
            context = {'map_html': map_html}
            return render(request, 'normal/map.html', context)
            
        else:
            place_name = place_name.lower()
            try:
                json_file_path = 'media/coordinates.json'
                with open(json_file_path, 'r') as file:
                    coordinates_data = json.load(file)
                coordinates = coordinates_data[place_name]["Coordinates"]
                location_geojson = {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "properties": {},
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": [coordinates]
                            }
                        }
                    ]
                }
                data_array = np.array(coordinates)
                mean = np.mean(data_array, axis=0)
                reverse = mean[::-1]
                place_location = reverse.tolist()
                location_map = folium.Map(location=place_location, zoom_start=10, tiles='OpenStreetMap', control_scale=True)
                location_map.get_root().html.add_child(folium.Element('<style>.leaflet-container { background-color: skyblue; filter: grayscale(60%); }</style>'))
                GeoJson(
                        location_geojson,
                        name=place_name,
                        style_function=lambda feature: {
                            'fillColor': 'skyblue',
                            'color': 'red',
                            'weight': 3,
                            'fillOpacity': 0.33,
                        },
                    ).add_to(location_map)
            except:
                return redirect("dashboard")
            
            event_locations = Event.objects.filter(date__gte=current_date)
            for i in event_locations:
                title = i.title
                latitude = i.latitude
                longitude = i.longitude
                event_coordinate = [latitude, longitude]
                distance = geodesic(place_location, event_coordinate).km
                radius_in_km = 100
                if distance <= radius_in_km:
                    folium.Marker(location=event_coordinate, popup=folium.Popup(f"{title} ", parse_html=True, show=True, permanent=True)).add_to(location_map)
            map_html = location_map._repr_html_()
            context = {'map_html': map_html}
            return render(request, 'normal/map.html', context)
    else:
        return redirect("dashboard")
        
def nearest(request):
    if request.method == 'POST':
        latitude = request.POST.get('latitude')
        print(latitude,"============================================")
        longitude = request.POST.get('longitude')
        print(latitude,"============================================")
        place_location = [latitude, longitude]
        current_date = date.today() 
        event_locations = Event.objects.filter(date__gte=current_date)

        distance_50km = []
        distance_50plus = []
        for i in event_locations:
            latitude = i.latitude
            longitude = i.longitude
            event_coordinate = [latitude, longitude]
            distance = geodesic(place_location, event_coordinate).km
            print(place_location)
            print(event_coordinate)
            print(distance)
            radius_in_km = 50

            event_data = {
                            'event': i,
                            'distance': distance,
                        }
            
            if distance <= radius_in_km:
                distance_50km.append(event_data)
            else:
                distance_50plus.append(event_data)
        context = {'distance_50km': distance_50km, 'distance_50plus': distance_50plus}
        return render(request, 'normal/nearest.html', context)
    