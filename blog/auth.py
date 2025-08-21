from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.exceptions import InvalidToken


# class CookieJWTAuthentication(JWTAuthentication):
#     def authenticate(self, request):
#         token = request.COOKIES.get('access_token')

#         if not token:
#             return None  # No token = anonymous user

#         try:
#             validated_token = self.get_validated_token(token)
#             return self.get_user(validated_token), validated_token
#         except AuthenticationFailed:
#             return None
        

### NEW HTTP-ONLY COOKIE AUTH ###
class CookieJWTAuthentication(JWTAuthentication):
    """
    Authenticate using Authorization header first; if missing, fall back to 'access_token' cookie.
    """
    def authenticate(self, request):
        """
        Try Authorization header first; if missing/invalid, fall back to 'access_token' cookie.
        """
        def authenticate(self, request):
            # 1) Try header
            header = self.get_header(request)
            if header:
                try:
                    return super().authenticate(request)
                except AuthenticationFailed:
                    # fall through to cookie
                    pass

        # Fallback to cookie
        raw_token = request.COOKIES.get('access_token')
        if not raw_token:
            return None

        try:
            validated = self.get_validated_token(raw_token)
        except InvalidToken as e:
            raise AuthenticationFailed("Invalid token in cookie") from e

        return (self.get_user(validated), validated)