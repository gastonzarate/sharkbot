"""Base urls"""

from django.contrib import admin
from django.urls import include, path

from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenBlacklistView, TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include(("tradings.urls", "tradings"))),
    path("", include(("accounts.urls", "accounts"))),
    path("api/auth/login/", TokenObtainPairView.as_view()),
    path("api/auth/login/refresh/", TokenRefreshView.as_view()),
    path("api/auth/logout/", TokenBlacklistView.as_view(), name="token_blacklist"),
    # API Documentation
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
