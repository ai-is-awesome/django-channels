from channels.auth iport AuthMiddlewareStack

from rest_framework.authtoken.models import Token

from django.contrib.auth.models import AnonymousUser



class TokenAuthMiddleware:

	def __init__(self, inner):
		self.inner = inner


	def __call__(self, scope):
		headers = dict(scope['headers'])

		if b'authorization' in headers:
			try:
				token_name, token_key = headers[b'authorization'].decode().split()

				if token_name == 'Token':
				token = Token.objects.get(key =token_key)

				scope['user'] = token.user
			except Token.DoesNotExist:
				scope['user'] = AnonymousUser()

		return self.inner(scope)
