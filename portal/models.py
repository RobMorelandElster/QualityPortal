from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
import hashlib
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
from django.core.exceptions import ObjectDoesNotExist

def utc_to_local(utc_dt):
	return utc_dt.replace(tzinfo=timezone.utc).astimezone(timezone.get_current_timezone())

class ElsterMeterTrack(models.Model):
	manufacture_number = models.CharField(max_length=100,  verbose_name="Manufacturer Number")
	serial_number = models.CharField(max_length=80,null=True, blank=True)
	manufacture_date = models.DateField(null=True, blank=True)
	purchase_date = models.DateField(null=True, blank=True)
	ship_date = models.DateField(null=True, blank=True)
	rma_number = models.CharField(max_length=100, null=True, blank=True, verbose_name="RMA Number (meter number)")
	rma_receive_date = models.DateField(null=True, blank=True)
	rma_complete_date = models.DateField(null=True, blank=True)
	defect_code = models.CharField(max_length=50,null=True,blank=True, verbose_name="Defect Code after root cause analysis")
	defect_code_desc = models.TextField(max_length=2000, verbose_name="Defect Code (description)",null=True, blank=True)
	remediation_action = models.CharField(max_length=50,null=True,blank=True, verbose_name="Elster remediation action")
	remediation_action_desc = models.TextField(max_length=2000, verbose_name="Elster remediation action (description)",null=True, blank=True)
	active = models.BooleanField(default=True)
	
	def __unicode__(self):
		return ("%s:%s:%s:%s"%(self.manufacture_number, str(self.rma_number), str(self.rma_receive_date), str(self.rma_complete_date)))

class CustomerMeterTrack(models.Model):
	NORTH = 'N'
	SOUTH = 'S'
	EAST = 'E'
	WEST = 'W'
	METER_EXPOSURE_CHOICES = (
		(NORTH, 'North'),
		(SOUTH, 'South'),
		(EAST, 'East'),
		(WEST, 'West'),
	)
	
	IN_FIELD = 'F'
	IN_INVENTORY = 'I'
	METER_SERVICE_CHOICES = (
		(IN_FIELD, 'In Field'),
		(IN_INVENTORY, 'Inventoried'),
	)
	number = models.CharField(max_length=100,  verbose_name="Meter Number")
	order_date = models.DateField(null=True, blank=True,verbose_name="Meter Order Date")
	set_date = models.DateField(null=True, blank=True,verbose_name="Meter Set Date")
	failure_date = models.DateField(null=True, blank=True,verbose_name="Meter Failure Date")
	system_failure_code = models.CharField(max_length=50,null=True,blank=True, verbose_name="System reference Defect Code")
	customer_defined_failure_code = models.CharField(max_length=50,null=True,blank=True, verbose_name="Customer reference Defect Code")
	failure_detail = models.TextField(max_length=2000, verbose_name="Detailed Description",null=True, blank=True)
	exposure = models.CharField(max_length = 1, null=True,blank=True, choices = METER_EXPOSURE_CHOICES, verbose_name="Meter Facing Direction")
	order_specs = models.CharField(max_length=100,  null=True,blank=True,verbose_name="Meter Order Specs")
	service_status = models.CharField(max_length = 1, null=True,blank=True, choices = METER_SERVICE_CHOICES, default=IN_INVENTORY, verbose_name="Meter Service Status")
	firmware_version = models.CharField(max_length=200,  verbose_name="Meter Firmware Version")
	longitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,verbose_name="Meter Longitude Position")
	latitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,verbose_name="Meter Latitude Position")
	
	def __unicode__(self):
		return ("%s:%s:%s:%s"%(self.number, str(self.order_date), str(self.failure_date), str(self.customer_defined_failure_code)))

