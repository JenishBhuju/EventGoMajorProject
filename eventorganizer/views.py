import asyncio
from django.shortcuts import render, redirect
from .models import Message
from authuser.models import CustomUser
from .models import Category, Event,Preference
from .forms import EventForm,UserPreferenceForm
from django.contrib.auth.decorators import login_required  
from django.shortcuts import render, redirect, get_object_or_404
import paho.mqtt.publish as publish


@login_required
def create_event(request):
    if request.method == 'POST':
        form = EventForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save(commit=False)
            event.user_id = request.user
            event.save()

            normal_users = CustomUser.objects.filter(user_type='normal')
            for user in normal_users:
                message_content = f"New event created: {event.title}"
                message = Message.objects.create(sender=request.user, recipient=user, event=event, content=message_content)

                publish.single(f"events/{user.username}", payload=message_content, hostname="localhost")


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
