from django.views.static import serve
from django.conf import settings

def multiserve(request, path, show_indexes=False):
    try:
        return serve(request, path, document_root=settings.MEDIA_ROOT, show_indexes=show_indexes)
    except:
        return serve(request, path, document_root=settings.UPLOAD_MEDIA_ROOT, show_indexes=show_indexes)

