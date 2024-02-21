import paho.mqtt.client as mqtt
from django.core.management.base import BaseCommand
from models import Event, Message
from authuser.models import CustomUser

class Command(BaseCommand):
    def handle(self, *args, **options):
        def on_message(client, userdata, msg):
            message_content = msg.payload.decode('utf-8')
            sender_username = msg.topic.split('/')[1]
            sender = CustomUser.objects.get(username=sender_username)
            recipient = CustomUser.objects.get(user_type='normal')

            event_title = message_content.split(":")[1].strip()
            event = Event.objects.get(title=event_title)

            Message.objects.create(sender=sender, recipient=recipient, event=event, content=message_content)

        client = mqtt.Client()
        client.on_message = on_message

        client.connect("localhost", 1883, 60)
        client.subscribe("events/+/")

        client.loop_forever()