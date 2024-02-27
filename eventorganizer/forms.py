from django import forms
from .models import Event, EventCategory, Preference, UserPreference

class EventForm(forms.ModelForm):
    latitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    longitude = forms.FloatField(widget=forms.HiddenInput(), required=False)
    class Meta:
        model = Event
        fields = ['title', 'description', 'logo', 'date', 'address','categories','latitude','longitude']
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'date': forms.DateInput(attrs={'type': 'date'})
        }
    
    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError('Title is required.')
        return title

    def clean_description(self):
        description = self.cleaned_data.get('description')
        if not description:
            raise forms.ValidationError('Description is required.')
        return description

    # def clean_logo(self):
    #     logo = self.cleaned_data.get('logo')
    #     if not logo:
    #         raise forms.ValidationError('Logo is required.')
    #     return logo

    def clean_date(self):
        date = self.cleaned_data.get('date')
        if not date:
            raise forms.ValidationError('Date is required.')
        return date

    def clean_address(self):
        address = self.cleaned_data.get('address')
        if not address:
            raise forms.ValidationError('Address is required.')
        return address

    def clean_categories(self):
        categories = self.cleaned_data.get('categories')
        if not categories:
            raise forms.ValidationError('At least one category must be selected.')
        return categories

    def clean_latitude(self):
        latitude = self.cleaned_data.get('latitude')
        if latitude is None:
            raise forms.ValidationError('Latitude is required.')
        return latitude

    def clean_longitude(self):
        longitude = self.cleaned_data.get('longitude')
        if longitude is None:
            raise forms.ValidationError('Longitude is required.')
        return longitude

    def save(self, commit=True):
        event = super().save(commit=commit)
        if commit:
            self._save_categories(event)
        return event

    def _save_categories(self, event):
        categories = self.cleaned_data.get('categories')
        existing_categories = EventCategory.objects.filter(event=event)
        existing_category_ids = set(existing_categories.values_list('category_id', flat=True))

        if categories:
            new_category_ids = set(categories.values_list('id', flat=True))
            removed_category_ids = existing_category_ids - new_category_ids
            added_category_ids = new_category_ids - existing_category_ids

            # Remove categories that are unselected
            EventCategory.objects.filter(event=event, category_id__in=removed_category_ids).delete()

            # Add new selected categories
            for category_id in added_category_ids:
                EventCategory.objects.create(event=event, category_id=category_id)
    
    def __init__(self, *args, **kwargs):
        super(EventForm, self).__init__(*args, **kwargs)
        # Check if 'user_id' field exists in the form instance
        if 'user_id' in self.fields:
            self.fields['user_id'].widget = forms.HiddenInput()  # Hide the user_id field
  
class UserPreferenceForm(forms.ModelForm):
    preferences = forms.ModelMultipleChoiceField(queryset=Preference.objects.all(), widget=forms.CheckboxSelectMultiple)
    
    class Meta:
        model = UserPreference
        fields = ['preferences']