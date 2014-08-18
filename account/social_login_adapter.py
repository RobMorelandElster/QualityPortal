from django.contrib.auth.models import User

from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class SocialAdapter(DefaultSocialAccountAdapter):
	def pre_social_login(self, request, sociallogin):
		# raise Exception
		try:
			user = User.objects.get(email=sociallogin.email_addresses[0])
			print user
			sociallogin.connect(request, user)
			# Create a response object
			raise ImmediateHttpResponse(response)
		except User.DoesNotExist:
			pass