from django.db import models
from django.core.validators import FileExtensionValidator
from authuser.models import CustomUser


validate_image_file_extension = FileExtensionValidator(
    allowed_extensions=['jpg', 'jpeg', 'png', 'gif']
)

class Event(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='events')
    logo = models.ImageField(upload_to='event_logos/',  validators=[validate_image_file_extension], null=True, blank=True)
    categories = models.ManyToManyField('Category', through='EventCategory')
    date = models.DateField(null=True, blank=True)  # Added date field with null and blank options
    address = models.CharField(max_length=200, null=True, blank=True)  # Added address field
    location = models.CharField(max_length=100)  # Storing location as string
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    def __str__(self):
        return self.title

class Category(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class EventCategory(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.event.title} - {self.category.name}"


class Preference(models.Model):
    name = models.CharField(max_length=100)
    img = models.ImageField(upload_to='preference_img/',  validators=[validate_image_file_extension], null=True, blank=True)
    def __str__(self):
        return f"{self.name}"



class UserPreference(models.Model):
    user_id = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user')
    preference_id = models.ForeignKey(Preference, on_delete=models.CASCADE, related_name='preferences')

    def __str__(self):
        return f"{self.user_id.full_name} - {self.preference_id.name}"

class Message(models.Model):
    sender = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='sent_messages')
    recipient = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='received_messages')
    event = models.ForeignKey(Event, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Message from {self.sender} to {self.recipient} about {self.event.title}"