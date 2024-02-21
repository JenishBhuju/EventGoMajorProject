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
from geopy.geocoders import Nominatim
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
        geolocator = Nominatim(user_agent="municipality_geolocation", timeout=10)
        location = geolocator.geocode(f'{place_name}, Nepal')
        if location:
            location = [(location.latitude), (location.longitude)]
            print(location)
            try:
                json_file_path = 'media/coordinates.json'
                # Open the JSON file
                with open(json_file_path, 'r') as file:
                    # Load the JSON data from the file
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
                # Create a map of give place name
                location_map = folium.Map(location=location, zoom_start=13, tiles='OpenStreetMap', control_scale=True)
                # Set the map background color and apply grayscale filter
                location_map.get_root().html.add_child(folium.Element('<style>.leaflet-container { background-color: skyblue; filter: grayscale(60%); }</style>'))
                # location_map.get_root().html.add_child(folium.Element('<style>.leaflet-container { filter: hue-rotate(100deg) brightness(90%) saturate(100%); }</style>'))
                # Add your GeoJson layer to the map
                GeoJson(location_geojson, name=place_name).add_to(location_map)
                # GeoJson(location_geojson,
                #         name=place_name,
                #         style_function=lambda x: {
                #         'fillColor': 'green',  # Change the fill color
                #         'color': 'red',  # Change the border color
                #         'weight': 2,  # Change the border width
                #         'fillOpacity': 0.5  # Change the fill opacity
                #         }).add_to(location_map)
            except:
                # Create a map of Kathmandu
                print("=========except=========")
                location_map = folium.Map(location=location, zoom_start=13, control_scale=True)
            # Example markers for three different locations
            # location1_coords = [27.7048, 85.3079]
            # location2_coords = [27.7172, 85.3270]
            # location3_coords = [27.6951, 85.3239]
            # folium.Marker(location=location1_coords, popup=folium.Popup('Location 1', parse_html=True, show=True, permanent=True)).add_to(location_map)
            # folium.Marker(location=location2_coords, popup=folium.Popup('Location 2', parse_html=True, show=True, permanent=True)).add_to(location_map)
            # folium.Marker(location=location3_coords, popup=folium.Popup('Location 3', parse_html=True, show=True, permanent=True)).add_to(location_map)
            map_html = location_map._repr_html_()
            context = {'map_html': map_html}
            return render(request, 'normal/map.html', context)
    else:
        location = [27.45, 85.20]
        location_map = folium.Map(location=location, zoom_start=8, tiles='OpenStreetMap', control_scale=True)
        location_map.get_root().html.add_child(folium.Element('<style>.leaflet-container { filter: hue-rotate(100deg) brightness(90%) saturate(100%); }</style>'))
        map_html = location_map._repr_html_()
        context = {'map_html': map_html}
        return render(request, 'normal/map.html', context)
    

    