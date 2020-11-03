from rest_framework_simplejwt import serializers as jwt_serializers
from rest_framework_simplejwt import views as jwt_views
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import datetime

class TokenObtainPairSerializer(jwt_serializers.TokenObtainPairSerializer):
    def get_token(self, user):
        token = RefreshToken.for_user(user)
        self.token = token 
        return token

    def validate(self, attrs):
        data = super(TokenObtainPairSerializer, self).validate(attrs)
        data['expires_on'] = datetime.now() + self.token.lifetime
        return data



class TokenRefreshSerializer(jwt_serializers.TokenRefreshSerializer):
    def get_token(self, user):
        token = RefreshToken.for_user(user)
        self.token = token 
        return token

    def validate(self, attrs):
        token = RefreshToken(attrs['refresh'])

        data = {
            'access': str(token.access_token),
            'expires_on': datetime.now() + token.lifetime,
        }
        return data



class TokenObtainPairView(jwt_views.TokenObtainPairView):
    serializer_class = TokenObtainPairSerializer



class TokenRefreshView(jwt_views.TokenRefreshView):
    serializer_class = TokenRefreshSerializer