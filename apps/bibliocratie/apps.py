from django.apps import AppConfig
import watson

class LivreSearchAdapter(watson.SearchAdapter):

    def get_title(self, obj):
        return obj.title

    def get_description(self, obj):
        return obj.excerpt

class BiblioConfig(AppConfig):
    name = "bibliocratie"
    def ready(self):
        BiblioUser = self.get_model("BiblioUser")
        BiblioUser._meta.get_field_by_name('email')[0]._unique=True
        watson.register(
            BiblioUser.objects.filter(is_active=True),
            store=("slug", "avatar_50x50_url","profil_url","username","class_name"),
            fields=("slug","username"),
        ),
        Livre = self.get_model("Livre")
        watson.register(
            Livre.objects.filter(phase__in=['GETMONEY','SUCCES','ECHEC','FEEDBACK'],is_active=True),
            store=("titre", "image_50x50_url","url","class_name"),
            fields=("titre", "tags__text",'resume','pourquoi_ce_livre','phrase_cle','annonces','biographie'),
        )
        UrlIndex = self.get_model("UrlIndex")
        watson.register(
            UrlIndex.objects.all(),
            store=("url", "texte",'titre','image_url',"class_name"),
        )
