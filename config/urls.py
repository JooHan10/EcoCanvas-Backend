from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('chat/', include("chat.urls")),
    path('campaigns/', include("campaigns.urls")),
    path('users/', include("users.urls")),
    path('payments/', include("payments.urls")),    
    path('shop/', include("shop.urls")),
]
