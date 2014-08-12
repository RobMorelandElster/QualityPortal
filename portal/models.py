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
	def __unicode__(self):
		return ("%s:%s:%s:%s"%(self.manufacture_number, str(self.rma_number), str(self.rma_receive_date), str(self.rma_complete_date)))

	OTHER = 'OT'
	GK = 'GK'
	METER_TYPES = (
		(OTHER, 'Non Gatekeeper'),
		(GK, 'Gatekeeper'),
	)
	
	manufacture_number = models.CharField(max_length=100,  verbose_name="Manufacturer Number")
	meter_type = models.CharField(max_length = 2, choices = METER_TYPES, default=OTHER, verbose_name="Meter Type")
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
	
	class Meta:
		unique_together = (("manufacture_number","rma_number"),)
		ordering = ["manufacture_number"]
		
	def clean(self):
		if self.manufacture_number is None:
			raise ValidationError('Manufacture Number must be filled in')
		elif len(self.manufacture_number) == 0:
			raise ValidationError('Manufacture Number must be filled in')
			
		# validate dates
		if self.purchase_date is not None and self.manufacture_date is not None:
			if self.purchase_date < self.manufacture_date:
				raise ValidationError('Purchase Date may not preceed Manufacture Date')
		
		if self.purchase_date is not None and self.ship_date is not None:
			if self.ship_date < self.purchase_date:
				raise ValidationError('Ship Date may not preceed Purchase Date')
				
		if self.rma_receive_date is not None and self.rma_complete_date is not None:
			if self.rma_complete_date < self.rma_receive_date:
				raise ValidationError('RMA Complete Date may not preceed RMA Receive Date')
				
		# validate defect entry
		if self.rma_complete_date is not None and self.defect_code is None:
			raise ValidationError('Defect Code may not be empty when RMA Complete Date is entered')
		if self.rma_complete_date is not None and self.defect_code is not None:
			if len(self.defect_code) ==0:
				raise ValidationError('Defect Code may not be empty when RMA Complete Date is entered')
				
		# meter_type validation
		if self.meter_type is not None:
			if self.meter_type != ElsterMeterTrack.GK and self.meter_type != ElsterMeterTrack.OTHER:
				raise ValidationError('Meter Type %s is invalid' %self.meter_type)
				
	
class CustomerMeterTrack(models.Model):
	def __unicode__(self):
		return ("%s:%s:%s:%s"%(self.number, str(self.order_date), str(self.failure_date), str(self.customer_defined_failure_code)))

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
	
	OTHER = 'OT'
	GK = 'GK'
	METER_TYPES = (
		(OTHER, 'Non Gatekeeper'),
		(GK, 'Gatekeeper'),
	)
	number = models.CharField(max_length=100,  verbose_name="Meter Number")
	meter_type = models.CharField(max_length = 2, choices = METER_TYPES, default=OTHER, verbose_name="Meter Type")
	order_date = models.DateField(null=True, blank=True,verbose_name="Meter Order Date")
	set_date = models.DateField(null=True, blank=True,verbose_name="Meter Set Date")
	failure_date = models.DateField(null=True, blank=True,verbose_name="Meter Failure Date")
	system_failure_code = models.CharField(max_length=50,null=True,blank=True, verbose_name="System reference Defect Code")
	customer_defined_failure_code = models.CharField(max_length=50,null=True,blank=True, verbose_name="Customer reference Defect Code")
	failure_detail = models.TextField(max_length=2000, verbose_name="Detailed Description",null=True, blank=True)
	exposure = models.CharField(max_length = 1, null=True,blank=True, choices = METER_EXPOSURE_CHOICES, verbose_name="Meter Facing Direction")
	order_specs = models.CharField(max_length=100,  null=True,blank=True,verbose_name="Meter Order Specs")
	service_status = models.CharField(max_length = 1, null=True,blank=True, choices = METER_SERVICE_CHOICES, default=IN_INVENTORY, verbose_name="Meter Service Status")
	firmware_version = models.CharField(max_length=200,  null=True,blank=True, verbose_name="Meter Firmware Version")
	longitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,verbose_name="Meter Longitude Position")
	latitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,verbose_name="Meter Latitude Position")
	
	class Meta:
		unique_together = (("number","failure_date"),)
		ordering = ["number"]
		
		
class UserProfile(models.Model):
	user = models.OneToOneField(User, related_name='profile')

	def __unicode__(self):
		#return "{}'s profile".format(self.user.username)
		return format(self.user.username)

	class Meta:
		db_table = 'user_profile'

	def account_verified(self):
		if self.user.is_authenticated:
			result = EmailAddress.objects.filter(email=self.user.email)
			if len(result):
				return result[0].verified
		return False

	def profile_image_url(self):
		fb_uid = SocialAccount.objects.filter(user_id=self.user.id, provider='facebook')
	
		if len(fb_uid):
			return "http://graph.facebook.com/{}/picture?width=40&height=40".format(fb_uid[0].uid)
	
		return "http://www.gravatar.com/avatar/{}?s=40".format(hashlib.md5(self.user.email).hexdigest())
	
	@staticmethod
	def default_user_profile():
		try:
			default_user_profile = UserProfile.objects.get(user__username='default')
		except ObjectDoesNotExist:
			default_user = User.objects.create(username='default', first_name='default', last_name='default')
			default_user.save()
			default_user_profile = UserProfile.objects.create(user=default_user)
			default_user_profile.save()
		return default_user_profile
	
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])