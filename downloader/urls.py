from django.urls import path
from . import views
from django.conf.urls.static import static
from django.conf import settings

urlpatterns = [
    path("", views.index, name="index"),
    path("posts", views.posts, name="posts"),
    path("reels", views.reels, name="reels"),
    path("allposts", views.allposts, name="allposts"),
    path("allreels", views.allreels, name="allreels"),
    path("login", views.login, name="login"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
