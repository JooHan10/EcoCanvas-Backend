from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include("chat.urls")),
    path('campaigns/', include("campaigns.urls")),
    path('users/', include("users.urls")),
    path('users/', include('allauth.urls')),  # 소셜로그인
    path('users/', include("dj_rest_auth.urls")),
    path('payments/', include("payments.urls")),
    path('shop/', include("shop.urls")),
    path('alarms/', include("alarms.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL,
                          document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL,
                          document_root=settings.STATIC_ROOT)
