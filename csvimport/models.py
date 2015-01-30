from django.db import models
from copy import deepcopy
from django.core.files.base import ContentFile
from django.core.cache import cache
#from django.core.files.storage import FileSystemStorage
from django.core.files.storage import default_storage
import re

from portal.models import *

#fs = FileSystemStorage(location=settings.MEDIA_ROOT)
CHOICES = (('manual', 'manual'), ('cronjob', 'cronjob'), ('rest-api', 'rest-api'),)

import uuid
import os

def get_file_path(instance, filename):
	try:
		ext = filename.split('.')[-1]
		base =filename.split('.')[-2] 
		filename = "%s-%s.%s" % (base, uuid.uuid4(), ext)
		return os.path.join('csv', filename)
	except:
		return filename
		   
class CSVImportElsterMeterTrack(models.Model):
	""" For importing portal.ElsterMeterTrack """

	upload_file = models.FileField(upload_to=get_file_path)
	file_name = models.CharField(max_length=255, blank=True)
	encoding = models.CharField(max_length=32, blank=True)
	upload_method = models.CharField(blank=False, max_length=50,
									 default='manual', choices=CHOICES)
	error_log = models.TextField(help_text='Each line is an import error')
	import_date = models.DateField(auto_now=True)
	import_user = models.CharField(max_length=255, default='anonymous',
								   help_text='User id as text', blank=True)
	def error_log_html(self):
		return re.sub('\n', '<br/>', self.error_log)
	error_log_html.allow_tags = True
	
	def __unicode__(self):
		return "id:%d-file:"%self.id + str(self.upload_file.name)


class CSVImportCustomerMeterTrack(models.Model):
	""" For importing portal.CustomerMeterTrack """

	upload_file = models.FileField(upload_to=get_file_path)
	file_name = models.CharField(max_length=255, blank=True)
	encoding = models.CharField(max_length=32, blank=True)
	upload_method = models.CharField(blank=False, max_length=50,
									 default='manual', choices=CHOICES)
	error_log = models.TextField(help_text='Each line is an import error')
	import_date = models.DateField(auto_now=True)
	import_user = models.CharField(max_length=255, default='anonymous',
								   help_text='User id as text', blank=True)
	
	def error_log_html(self):
		return re.sub('\n', '<br/>', self.error_log)
	error_log_html.allow_tags = True
	
	def __unicode__(self):
		return self.upload_file.name

# Receive the pre_delete signal and delete the file associated with the model instance.
from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

@receiver(pre_delete, sender=CSVImportCustomerMeterTrack)
def mymodel_delete_customer_file(sender, instance, **kwargs):
    print "delete %s"% instance.upload_file
    default_storage.delete(instance.file_name)
    # Pass false so FileField doesn't save the model.
    instance.upload_file.delete(False)
    
@receiver(pre_delete, sender=CSVImportElsterMeterTrack)
def mymodel_delete_elster_file(sender, instance, **kwargs):
    print "delete %s"% instance.upload_file
    default_storage.delete(instance.file_name)
    # Pass false so FileField doesn't save the model.
    instance.upload_file.delete(False)