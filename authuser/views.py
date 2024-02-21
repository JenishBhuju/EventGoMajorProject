# In your Django app's views.py

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.urls import reverse
from eventorganizer.forms import UserPreferenceForm
from eventorganizer.models import Event, Preference, UserPreference
from .forms import CustomUserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.urls import reverse

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if user.user_type == 'organizer':
                return redirect('event-list')  # Redirect to event list if user is an organizer
            elif user.user_type == 'normal':
                user_preferences = UserPreference.objects.filter(user_id=user)
                if user_preferences.exists():  # Check if the user has preferences
                    return redirect('dashboard')  # Redirect to dashboard if preferences exist
                else:
                    return redirect('save_preferences')  # Redirect to save preferences if no preferences exist
    return render(request, 'login.html')

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)  # Save the form data without committing to the database yet
            user.password = make_password(form.cleaned_data['password'])  # Explicitly hash the password
            user.save()  # Now save the user with the hashed password
            return redirect('login') 
    else:
        form = CustomUserCreationForm()
    return render(request, 'register.html', {'form': form})

def logout_view(request):
    logout(request)
    # Redirect to a specific URL after logout
    return redirect('login')

@login_required
def event_list(request):
    # Retrieve events related to the logged-in user
    events = Event.objects.filter(user_id=request.user)
    return render(request, 'organizer/event_list.html', {'events': events})

@login_required
def dashboard(request):
    # Get the logged-in user
    user = request.user
    
    # Get user preferences
    user_preferences = UserPreference.objects.filter(user_id=user)
    user_category_names = [preference.preference_id.name for preference in user_preferences]
    
    # Filter events based on user preferences
    matched_events = []
    unmatched_events = []
    for event in Event.objects.all():
        event_category_names = event.categories.values_list('name', flat=True)
        if any(category_name in user_category_names for category_name in event_category_names):
            matched_events.append(event)
        else:
            unmatched_events.append(event)
    
    return render(request, 'normal/dashboard.html', {'matched_events': matched_events, 'unmatched_events': unmatched_events})

def save_user_preferences(request):
    preferences = Preference.objects.all()  # Retrieve all preferences
    if request.method == 'POST':
        form = UserPreferenceForm(request.POST)
        if form.is_valid():
            user = request.user  # Assuming you have a logged-in user
            selected_preferences = form.cleaned_data.get('preferences')
            for preference in selected_preferences:
                UserPreference.objects.create(user_id=user, preference_id=preference)
            return redirect('dashboard')  # Redirect to preference list page
    else:
        form = UserPreferenceForm()
    return render(request, 'normal/save_preferences.html', {'form': form, 'preferences': preferences})

def update_preferences(request):
    user = request.user
    preferences = Preference.objects.all()
    initial_preferences = user.user.values_list('preference_id', flat=True)
    if request.method == 'POST':
        form = UserPreferenceForm(request.POST)
        if form.is_valid():
            # Delete existing preferences for the user
            UserPreference.objects.filter(user_id=user).delete()
            # Save new preferences
            selected_preferences = form.cleaned_data.get('preferences')
            for preference in selected_preferences:
                UserPreference.objects.create(user_id=user, preference_id=preference)
            return redirect('dashboard')  # Redirect to dashboard or any other desired page
    else:
        form = UserPreferenceForm(initial={'preferences': initial_preferences})
    return render(request, 'normal/update_preferences.html', {'form': form, 'preferences': preferences})