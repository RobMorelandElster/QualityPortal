# -*- coding: utf-8 -*-
from __future__ import absolute_import

import warnings

from django import forms
from django.core.exceptions import ValidationError
import datetime
from django.utils import timezone

from django.forms.models import ModelForm
from portal.models import *

import autocomplete_light
autocomplete_light.autodiscover()

class ElsterMeterTrackForm(ModelForm):
	complaint = forms.CharField(widget=forms.Textarea())
	finding =  forms.CharField(widget=forms.Textarea())
	action_taken =  forms.CharField(widget=forms.Textarea())
	class Meta:
			model = ElsterMeterTrack
			fields = '__all__'

class CustomerMeterTrackForm(ModelForm):
	class Meta:
			model = CustomerMeterTrack
			fields = '__all__'
		
class ElsterMeterTrackSearchForm(forms.Form):
	search_type = forms.ChoiceField(widget = forms.Select(
							attrs={"onChange":"choiceChange()"}),
							choices = ([('date_range','Date Range'), ('rma_number','RMA'),('record','Serial-Barcode'), ]))
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
								
	meter_track_record =  forms.CharField(required=False,
								label="Serial/Barcode",
								help_text = "Choose Record by Serial or Barcode",
								widget=autocomplete_light.TextWidget('ElsterMeterTrackAutocomplete'))

	def clean_start_date(self):
		data = self.cleaned_data['start_date']
		st = self.cleaned_data['search_type']
		if data == None and (st in 'date_range'):
			raise forms.ValidationError("Choose an start date")
		# Always return the cleaned data, whether you have changed it or
		# not.
		return data

	def clean_end_date(self):
		data = self.cleaned_data['end_date']
		st = self.cleaned_data['search_type']

		if data == None and (st in 'date_range'):
			raise forms.ValidationError("Choose an end date")
		# Always return the cleaned data, whether you have changed it or
		# not.
		return data
		
	def clean_meter_track_record(self):
		data = self.cleaned_data['meter_track_record']
		st = self.cleaned_data['search_type']

		if data == None and (st in 'record'):
			raise forms.ValidationError("Choose an Serial#/Barcode")
		if len(data) == 0 and (st in 'record'):
			raise forms.ValidationError("Choose an Serial#/Barcode")
		if len(data.split('/')) != 2 and (st in 'record'):
			raise forms.ValidationError("Choose an Serial#/Barcode")
		# Always return the cleaned data, whether you have changed it or
		# not.
		return data

	def clean_rma_number(self):
		data = self.cleaned_data['rma_number']
		st = self.cleaned_data['search_type']
		
		if (st in'rma_number') and data == None:
				raise forms.ValidationError("Enter RMA")
		elif (st in 'rma_number') and len(data) == 0:
				raise forms.ValidationError("Enter RMA")

		return data
		
	def clean_meter_track_record(self):
		data = self.cleaned_data['meter_track_record']
		st = self.cleaned_data['search_type']

		if data == None and (st in 'record'):
			raise forms.ValidationError("Choose a serial number or barcode")
		# Always return the cleaned data, whether you have changed it or
		# not.
		return data