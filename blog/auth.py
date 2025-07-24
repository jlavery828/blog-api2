from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        token = request.COOKIES.get('access_token')

        if not token:
            return None  # No token = anonymous user

        try:
            validated_token = self.get_validated_token(token)
            return self.get_user(validated_token), validated_token
        except AuthenticationFailed:
            return None