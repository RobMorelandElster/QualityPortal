from __future__ import absolute_import

from celery import shared_task
from datetime import datetime
import datetime
from django.core.exceptions import ObjectDoesNotExist
from django.db import IntegrityError
import time

from csvimport.models import CSVImportElsterMeterTrack, CSVImportCustomerMeterTrack

@shared_task (bind=True)
def processElsterMeterTrackImportFile(self, defaults, obj, user):
	try:
		from csvimport.management.commands.elstermetertrackcsvimport import Command
		cmd = Command()
		obj.file_name = str(obj.upload_file)
		cmd.setup( uploaded = obj.file_name, defaults = defaults)
		errors = cmd.run(logid = obj.id)
		obj.error_log = obj.error_log + "\nNew Task ID: %s\n"%str(self.request.id)
		if errors:
			obj.error_log = obj.error_log +'\n'.join(errors)
		obj.import_user = str(user)
		obj.import_date = datetime.datetime.now()
		try:
		    obj.save()
		except IntegrityError:
		    obj.update()
	except Exception as inst:
		obj.error_log = obj.error_log + '\nImport Error in background task: %s'% str(inst)
		try:
		    obj.save()
		except IntegrityError:
		    obj.update()
	return obj.error_log
	
@shared_task (bind=True)
def processCustomerMeterTrackImportFile(self, defaults, obj, user):
	try:
		from csvimport.management.commands.customermetertrackcsvimport import Command
		cmd = Command()
		obj.file_name = str(obj.upload_file)
		cmd.setup( uploaded = obj.file_name, defaults = defaults)
		errors = cmd.run(logid = obj.id)
		obj.error_log = obj.error_log + "\nNew Task ID: %s\n"%str(self.request.id)
		if errors:
			obj.error_log = obj.error_log +'\n'.join(errors)
		obj.import_user = str(user)
		obj.import_date = datetime.datetime.now()
		try:
		    obj.save()
		except IntegrityError:
		    obj.update()
	except Exception as inst:
		obj.error_log = obj.error_log + '\nImport Error in background task: %s'% str(inst)
		try:
		    obj.save()
		except IntegrityError:
		    obj.update()
	return obj.error_log