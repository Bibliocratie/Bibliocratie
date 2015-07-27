__author__ = 'Exlivris3'

from django.core.management.base import BaseCommand, CommandError
from ws4redis.publisher import RedisPublisher
from ws4redis.redis_store import RedisMessage
from bibliocratie.models import Notification
from bibliocratie.serializers import NotificationApiSerializer
from rest_framework.renderers import JSONRenderer


class Command(BaseCommand):
    help = 'envoyer une notification'

    def add_arguments(self, parser):
        parser.add_argument('message', type=str, nargs='?',
                     help="Message a notifier")
        parser.add_argument('user', type=str, nargs='?',
                     help="user a notifier")

    def handle(self, *args, **options):
        message = options['message']
        user = options['user']
        notification = Notification(image="",texte=message)
        redisMessage = RedisMessage(JSONRenderer().render(NotificationApiSerializer(notification).data))
        RedisPublisher(facility='user', users=[user,]).publish_message(redisMessage)

