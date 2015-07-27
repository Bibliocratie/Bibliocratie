import django.dispatch

commande_changes_status = django.dispatch.Signal(providing_args=["commande", "timestamp"])

souscription_changes_status = django.dispatch.Signal(providing_args=["souscription", "timestamp"])

livre_changes_phase = django.dispatch.Signal(providing_args=["livre", "timestamp"])

user_disconnected = django.dispatch.Signal(providing_args=["user", "timestamp"])
