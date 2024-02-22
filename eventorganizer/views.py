import asyncio
from django.shortcuts import render, redirect
from .models import Message
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

@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.user_id = request.user
            event.save()

            # normal_users = CustomUser.objects.filter(user_type='normal')
            # for user in normal_users:
            #     message_content = f"New event created: {event.title}"
            #     message = Message.objects.create(sender=request.user, recipient=user, event=event, content=message_content)

            #     publish.single(f"events/{user.username}", payload=message_content, hostname="localhost")


            form._save_categories(event)
           
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
            return redirect('event-list')
    else:
        form = EventForm(instance=event)
    return render(request, 'organizer/update_event.html', {'form': form, 'event': event})

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(Event, pk=event_id)
    is_organizer = request.user.is_organizer
    return render(request, 'organizer/event_detail.html', {'event': event, 'is_organizer': is_organizer})

def event_search(request):
    query = request.GET.get('q')
    category = request.GET.get('category')

    # Get all events
    events = Event.objects.all()

    # Apply filters if provided
    if query:
        events = events.filter(title__icontains=query) | events.filter(description__icontains=query)

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

    if request.method == 'POST':
        place_name = request.POST.get('place_name')
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
            return redirect("map-show")
        
        event_locations = Event.objects.all()
        for i in event_locations:
            title = i.title
            description = i.description
            latitude = i.latitude
            longitude = i.longitude
            event_coordinate = [latitude, longitude]
            distance = geodesic(place_location, event_coordinate).km
            radius_in_km = 100
            if distance <= radius_in_km:
                folium.Marker(location=event_coordinate, popup=folium.Popup(f"{title} : {description}", parse_html=True, show=True, permanent=True)).add_to(location_map)
        map_html = location_map._repr_html_()
        context = {'map_html': map_html}
        return render(request, 'normal/map.html', context)
    
    else:
        location = [28.267940179261373, 84.254150390625]
        location_map = folium.Map(location=location, zoom_start=7, tiles='OpenStreetMap', control_scale=True)
        location_map.get_root().html.add_child(folium.Element('<style>.leaflet-container { filter: hue-rotate(100deg) brightness(90%) saturate(100%); }</style>'))
        locations = Event.objects.all()
        for i in locations:
            title = i.title
            description = i.description
            latitude = i.latitude
            longitude = i.longitude
            location_coords = [latitude, longitude]
            folium.Marker(location=location_coords, popup=folium.Popup(f"{title} : {description}", parse_html=True, show=True, permanent=True)).add_to(location_map)
        map_html = location_map._repr_html_()
        context = {'map_html': map_html}
        return render(request, 'normal/map.html', context)
    
