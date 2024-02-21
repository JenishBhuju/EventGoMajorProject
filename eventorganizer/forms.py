from django import forms
from .models import Event, EventCategory, Preference, UserPreference

class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'logo', 'date', 'address','categories']
        widgets = {
            'categories': forms.CheckboxSelectMultiple(),
            'date': forms.DateInput(attrs={'type': 'date'})
        }

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