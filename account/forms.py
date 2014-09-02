from __future__ import absolute_import

import warnings

from django import forms
from django.core.exceptions import ValidationError
from django.forms import CharField, HiddenInput
from django.utils.translation import ugettext_lazy as _
from portal.models import  UserProfile, Account
from captcha.fields import CaptchaField

	
class SignupForm(forms.Form):
	first_name = forms.CharField(max_length=25, label='First Name')
	last_name = forms.CharField(max_length=25, label='Last Name')
	account_name = forms.CharField(max_length=25, label='Account Name', required=True)
	account_verifification_key = forms.CharField(max_length=25, label="Account Verification Code", required=True)
	show_your_not_a_robot = CaptchaField()
	
	def signup(self, request, user):
		acct = Account.objects.filter(
			name = self.cleaned_data['account_name'],
			verification = self.cleaned_data['account_verifification_key'],
			)
		if len(acct) <> 0:		
			user.first_name = self.cleaned_data['first_name']
			user.last_name = self.cleaned_data['last_name']
			user.save()
			up = UserProfile(user=user)
			up.save()
			# Associate existing account with new user
			#acct[0].holder = up
			#acct[0].save()
		return user	
		
	def clean_account_name(self):
		try:
			data = self.cleaned_data.get('account_name')
			if not data:
				raise forms.ValidationError('account name cannot be blank')
		except KeyError:
			raise forms.ValidationError('account name cannot be blank')
		return data
		
	def clean_account_verification_key(self):
		try:
			data = self.cleaned_data.get('account_verifification_key')
			if not data:
				raise forms.ValidationError('account verification key cannot be blank')
		except KeyError:
			raise forms.ValidationError('account verification key cannot be blank')
		return data
			
	def clean(self):
		try:
			an = self.cleaned_data.get('account_name')
			avk = self.cleaned_data['account_verifification_key']
		except KeyError:
			raise ValidationError('All fields required')
			return self.cleaned_data
	
		if (an and avk):
			acct = Account.objects.filter(
				name = an,
				verification = avk,
				)
			if len(acct) == 0:	
				raise ValidationError('No account matching account name %s and verification %s' % (self.cleaned_data['account_name'], self.cleaned_data['account_verifification_key']))
		else:
			raise ValidationError('All fields required')

		return self.cleaned_data