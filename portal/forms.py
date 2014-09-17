# -*- coding: utf-8 -*-
from __future__ import absolute_import

import warnings

from django import forms
from django.core.exceptions import ValidationError
import datetime
from django.utils import timezone

from django.forms.models import ModelForm
from portal.models import *

class ElsterMeterTrackForm(ModelForm):
	class Meta:
			model = ElsterMeterTrack
			fields = '__all__'

class CustomerMeterTrackForm(ModelForm):
	class Meta:
			model = CustomerMeterTrack
			fields = '__all__'
		
class ElsterMeterTrackSearchForm(forms.Form):
	start_date = forms.DateField(widget=forms.TextInput(attrs=
								{
									'class':'datepicker'
								}), 
								label="Choose start date",
								help_text='Choose a beginning date or leave blank',
								required=False,
								initial=datetime.date.today,)
								
	end_date = forms.DateField(widget=forms.TextInput(attrs=
								{
									'class':'datepicker'
								}), 
								label="Choose end date",
								help_text='Choose a ending date or leave blank',
								required=False,
								initial=datetime.date.today,)
								
	rma_number = forms.CharField(required=False,
								label="RMA Number",
								help_text="Enter RMA or leave blank",)

	def clean_start_date(self):
		data = self.cleaned_data['start_date']
		if data:
			if datetime.date.today() < data:
				raise forms.ValidationError("Don't choose a future date")
		# Always return the cleaned data, whether you have changed it or
		# not.
		return data

	def clean_end_date(self):
		data = self.cleaned_data['end_date']
		s_date = None
		try:
			s_date = self.cleaned_data['start_date']
		except:
			pass
		if data == None and s_date != None:
			raise forms.ValidationError("Choose an end date")
		# Always return the cleaned data, whether you have changed it or
		# not.
		return data

	def clean_rma_number(self):
		data = self.cleaned_data['rma_number']
		b_date = None
		e_date = None
		try:
			b_date = self.cleaned_data['start_date']
			e_date = self.cleaned_data['end_date']
		except:
			pass
		if len(data):
			if b_date or  e_date:
				raise forms.ValidationError("Only enter RMA if Dates are not set")
		return data