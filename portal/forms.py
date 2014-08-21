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
		


DISPLAY_PERIOD = (('01', 'Day'), ('07', 'Week'),('30', 'Month'))

class ElsterMeterTrackSearchForm(forms.Form):
	
	start_date = forms.DateField(widget=forms.TextInput(attrs=
								{
									'class':'datepicker'
								}), 
								label="Choose start date",
								help_text='Choose a beginning date',
								required=True,
								initial=datetime.date.today,)
								
	period = forms.ChoiceField(required=True,
								widget=forms.RadioSelect, 
								choices=DISPLAY_PERIOD, 
								initial='01',
								label="Choose period to display",)
								
	rma_number = forms.CharField(required=False,
								label="RMA Number",
								help_text="Enter RMA or leave blank",)
								
	def clean_start_date(self):
		data = self.cleaned_data['start_date']
		if datetime.date.today() < data:
			raise forms.ValidationError("Don't choose a future date")
	
		# Always return the cleaned data, whether you have changed it or
		# not.
		return data