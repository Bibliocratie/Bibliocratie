from django.contrib.auth import logout
# from django.contrib import messages
import datetime
from django.utils import timezone
from django.conf import settings

from bibliocratie.signals import user_disconnected

class SessionIdleTimeout:
    """Middleware class to timeout a session after a specified time period.
    """
    def process_request(self, request):
        # Timeout is done only for authenticated logged in users.
        if request.user.is_authenticated():
            current_datetime = datetime.datetime.now()

            # Timeout if idle time period is exceeded.
            if request.session.has_key('last_activity') and \
                (current_datetime - request.session['last_activity']).seconds > \
                settings.SESSION_IDLE_TIMEOUT:
                user=request.user
                if not user.is_staff:
                    logout(request)
                    user_disconnected.send(sender=self.__class__, user=user, timestamp=timezone.now())
                # messages.add_message(request, messages.ERROR, 'Your session has been timed out.')
            # Set last activity time in current session.
            else:
                request.session['last_activity'] = current_datetime
        return None
