# -*- coding: utf-8 -*-

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