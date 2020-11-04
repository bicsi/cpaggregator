from rest_framework_simplejwt import serializers as jwt_serializers
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime
from rest_framework_simplejwt.settings import api_settings

class TokenObtainPairSerializer(jwt_serializers.TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super(TokenObtainPairSerializer, self).validate(attrs)
        data['expires_on'] = datetime.now() + api_settings.ACCESS_TOKEN_LIFETIME
        return data



class TokenRefreshSerializer(jwt_serializers.TokenRefreshSerializer):
    def validate(self, attrs):
        data = super(TokenRefreshSerializer, self).validate(attrs)
        data['expires_on'] = datetime.now() + api_settings.ACCESS_TOKEN_LIFETIME
        return data



class TokenObtainPairView(jwt_views.TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer



class TokenRefreshView(jwt_views.TokenRefreshView):
    serializer_class = TokenRefreshSerializer