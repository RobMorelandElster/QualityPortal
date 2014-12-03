from datetime import datetime
import datetime
from django import forms
from django.db import models
from django.contrib import admin
from django.contrib.admin import ModelAdmin
import os
from csvimport.models import *
from portal.models import *
	
	
ELSTER_METER_TRACK_CONTENT_HELP_TEXT = ' '.join(['<p>Assumes the following comma separated fields (all text fields should be double quoted):<br/>'
		'elster_serial_number, meter_style, meter_barcode, manufacture_date, rma_number, rma_create_date, rma_receive_date, rma_complete_date, defect_code, defect_code_desc, complaint, finding, action_taken<br/>'
		'where: elster_serial_number is the elster_manufacture_serial number for the device, represented as a text field<br/>'
		'meter_style is the elster style number for the device represented as a text field<br/>'
		'meter_barcode is the faceplate barcode scanned from the device represented as a text field<br/>'
		'manufacture_date is the date of manufacture represented as YYYY-MM-DD<br/>'
		'rma_number is the RMA Number represented as a text field<br/>'
		'rma_create_date is the date the rma was created represented as YYYY-MM-DD<br/>'
		'rma_receive_date is the date the device was received by Elster for the RMA process represented as YYYY-MM-DD<br/>'
		'rma_complete_date is the date the rma is completed by Elster represented as YYYY-MM-DD<br/>'
		'defect_id is a positive integer value representing an Elster defect code<br/>'
		'defect_id_desc is the description of the defect represented as a text field<br/>'
		'complaint is the Customer Complaint represented as a text field<br/>'
		'finding is the technicians determination  represented as a text field<br/>'
		'action_taken is the Elster action taken from the rma  represented as a text field<br/>',])

class CSVImportElsterMeterTrackAdmin(ModelAdmin):
	#change_form_template = 'progressbarupload/change_form.html'
	#add_form_template = 'progressbarupload/change_form.html'
	
	readonly_fields = ['file_name',
					   'upload_method',
					   'error_log_html',
					   'import_user']
	fieldsets = [
				#('Organization Name', {'fields':('organization_name',),}),
				('Upload file', {
					'fields':('upload_file',),
					'description': '<div class="help">%s</div>' % ELSTER_METER_TRACK_CONTENT_HELP_TEXT,
				}),
				('Elster Meter Track Import Details',
					{'fields':                
						('file_name',
						'upload_method',
						'error_log_html',
						'import_user',),
					},),
				]

	formfield_overrides = {models.CharField: {'widget': forms.Textarea(attrs={'rows':'4','cols':'60'})},}
	list_display = ['file_name', 'import_date', 'import_user', 'error_log_html']
	search_fields = ['import_user', 'file_name']

	def save_model(self, request, obj, form, change):
		""" Do save and process command - cant commit False
			since then file wont be found for reopening via right charset
		"""
		form.save()
		from csvimport.management.commands.elstermetertrackcsvimport import Command
		cmd = Command()
		if obj.upload_file:
			obj.file_name = str(obj.upload_file)
			#obj.encoding = ''
			defaults = 'utf-8'
			cmd.setup( # org = obj.organization_name,
					uploaded = obj.file_name,
					defaults = defaults)
		errors = cmd.run(logid = obj.id)
		if errors:
			obj.error_log = '\n'.join(errors)
		obj.import_user = str(request.user)
		obj.import_date = datetime.datetime.now()
		obj.save()

	def filename_defaults(self, filename):
		""" Override this method to supply filename based data """
		defaults = []
		splitters = {'/':-1, '.':0, '_':0}
		filename = str(filename)
		for splitter, index in splitters.items():
			if filename.find(splitter)>-1:
				filename = filename.split(splitter)[index]
		return defaults

	
CUSTOMER_METER_TRACK_CONTENT_HELP_TEXT = ' '.join(['<p>Assumes the following comma separated fields (all text fields should be double quoted):<br/>'
		'elster_meter_serial_number, meter_type, meter_barcode, order_date, set_date, failure_date, reason_for_removal, customer_defined_failure_code, failure_detail, exposure, ship_date, tracking_number, service_status, original_order_information,longitude, latitude, address<br/>'
		'where: elster_meter_serial_number is the elster_manufacture_serial number for the device, represented as a text field<br/>'
		'meter_type is the elster style number for the device represented as a text field<br/>'
		'meter_barcode is the faceplate barcode scanned from the device represented as a text field<br/>'
		'order_date is the date of order or receipt by customer represented as YYYY-MM-DD<br/>'
		'set_date is the date of field deployment represented as YYYY-MM-DD<br/>'
		'failure_date is the date of recognized failure or removal represented as YYYY-MM-DD<br/>'		
		'reason_for_removal is a short description for removal represented as a text field<br/>'
		'customer_defined_failure_code is customer defined failure code represented as a text field (max 50 characters)<br/>'
		'failure_detail is a place to record more detail than the abbreviated failure (max 2000 characters)<br/>'
		'exposure is the compass direction the meter is facing (single character N, S, E or W)<br/>'
		'shipment_reference is the reference number for the shipment meter returned to Elster represented as a text field (max 25 characters)<br/>'
		'original_order_information is contains any original meter order information you may wish to track for the device represented as a text field (max 100 characters)<br/>'
		'longitude is the longitude of the field location for the device (12 digits 6 decimal places)<br/>'
		'latitude is the latitude of the field location for the device (12 digits 6 decimal places)<br/>'
		'address is the full address (if allowed) represented as a text field (max 2000 characters)<br/>',])

class CSVImportCustomerMeterTrackAdmin(ModelAdmin):
	#change_form_template = 'progressbarupload/change_form.html'
	#add_form_template = 'progressbarupload/change_form.html'
	
	readonly_fields = ['file_name',
					   'upload_method',
					   'error_log_html',
					   'import_user']
	fieldsets = [
				#('Organization Name', {'fields':('organization_name',),}),
				('Upload file', {
					'fields':('upload_file',),
					'description': '<div class="help">%s</div>' % CUSTOMER_METER_TRACK_CONTENT_HELP_TEXT,
				}),
				('Customer Meter Track Import Details',
					{'fields':                
						('file_name',
						'upload_method',
						'error_log_html',
						'import_user',),
					},),
				]

	formfield_overrides = {models.CharField: {'widget': forms.Textarea(attrs={'rows':'4','cols':'60'})},}
	list_display = ['file_name', 'import_date', 'import_user', 'error_log_html']
	search_fields = ['import_user', 'file_name']

	def save_model(self, request, obj, form, change):
		""" Do save and process command - cant commit False
			since then file wont be found for reopening via right charset
		"""
		form.save()
		from csvimport.management.commands.customermetertrackcsvimport import Command
		cmd = Command()
		if obj.upload_file:
			obj.file_name = str(obj.upload_file)
			#obj.encoding = ''
			defaults = 'utf-8'
			cmd.setup( # org = obj.organization_name,
					uploaded = obj.file_name,
					defaults = defaults)
		errors = cmd.run(logid = obj.id)
		if errors:
			obj.error_log = '\n'.join(errors)
		obj.import_user = str(request.user)
		obj.import_date = datetime.datetime.now()
		obj.save()

	def filename_defaults(self, filename):
		""" Override this method to supply filename based data """
		defaults = []
		splitters = {'/':-1, '.':0, '_':0}
		filename = str(filename)
		for splitter, index in splitters.items():
			if filename.find(splitter)>-1:
				filename = filename.split(splitter)[index]
		return defaults

admin.site.register(CSVImportElsterMeterTrack, CSVImportElsterMeterTrackAdmin)
admin.site.register(CSVImportCustomerMeterTrack, CSVImportCustomerMeterTrackAdmin)
