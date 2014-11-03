#import autocomplete_light
#autocomplete_light.autodiscover()

from django.contrib import admin

# Register your models here.
from models import *

from django import forms

from datetime import date

from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse

import csv
from django.utils.encoding import smart_str

class ElsterMeterRmaCreateListFilter(SimpleListFilter):
	# Human-readable title which will be displayed in the
	# right admin sidebar just above the filter options.
	title = _('rma_create_date')

	# Parameter for the filter that will be used in the URL query.
	parameter_name = 'rma_create_date'

	def lookups(self, request, model_admin):
		"""
		Returns a list of tuples. The first element in each
		tuple is the coded value for the option that will
		appear in the URL query. The second element is the
		human-readable name for the option that will appear
		in the right sidebar.
		"""
		return (
			('30', _('in past month')),
			('90', _('in past quarter')),
			('180', _('in past six months')),
		)

	def queryset(self, request, queryset):
		"""
		Returns the filtered queryset based on the value
		provided in the query string and retrievable via
		`self.value()`.
		"""
		now = timezone.now()
		
		if self.value() == '30':
			return queryset.filter(rma_create_date__gte=now-datetime.timedelta(days=30))
		if self.value() == '90':
			return queryset.filter(rma_create_date__gte=now-datetime.timedelta(days=90))
		if self.value() == '180':
			return queryset.filter(rma_create_date__gte=now-datetime.timedelta(days=180))

class ElsterMeterRmaCompleteListFilter(SimpleListFilter):
	# Human-readable title which will be displayed in the
	# right admin sidebar just above the filter options.
	title = _('rma_complete_date')

	# Parameter for the filter that will be used in the URL query.
	parameter_name = 'rma_complete_date'

	def lookups(self, request, model_admin):
		"""
		Returns a list of tuples. The first element in each
		tuple is the coded value for the option that will
		appear in the URL query. The second element is the
		human-readable name for the option that will appear
		in the right sidebar.
		"""
		return (
			('30', _('in past month')),
			('90', _('in past quarter')),
			('OPEN', _('Uncompleted')),
		)

	def queryset(self, request, queryset):
		"""
		Returns the filtered queryset based on the value
		provided in the query string and retrievable via
		`self.value()`.
		"""
		now = timezone.now()
		
		if self.value() == '30':
			return queryset.filter(rma_complete_date__gte=now-datetime.timedelta(days=30))
		if self.value() == '90':
			return queryset.filter(rma_complete_date__gte=now-datetime.timedelta(days=90))
		if self.value() == 'OPEN':
			return queryset.filter(rma_complete_date__isnull=True)

def export_elster_meter_track_csv(modeladmin, request, queryset):
	response = HttpResponse(mimetype='text/csv')
	response['Content-Disposition'] = 'attachment; filename=elster_meter_track.csv'
	writer = csv.writer(response, csv.excel)
	response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
	writer.writerow([
		smart_str(u'elster_serial_number'), 
		smart_str(u'meter_style'),
		smart_str(u'meter_barcode'), 
		smart_str(u'manufacture_date'), 
		smart_str(u'rma_number'),
		smart_str(u'rma_create_date'),
		smart_str(u'rma_receive_date'), 
		smart_str(u'rma_complete_date'), 		
		smart_str(u'defect_id_desc'),
		smart_str(u'complaint'),
		smart_str(u'finding'),
		smart_str(u'action_taken'),
		])
	for obj in queryset:
		
		writer.writerow([
			smart_str(obj.elster_serial_number),
			smart_str(obj.meter_style.description),
			smart_str(obj.meter_barcode),
			smart_str(obj.manufacture_date),
			smart_str(obj.rma_number),
			smart_str(obj.rma_create_date),
			smart_str(obj.rma_receive_date),
			smart_str(obj.rma_complete_date),
			smart_str(obj.defect.description),
			smart_str(obj.complaint),
			smart_str(obj.finding),
			smart_str(obj.action_taken),
		])
	return response
export_elster_meter_track_csv.short_description = u"Export Elster Meters CSV"


class ElsterMeterTrackAdmin(admin.ModelAdmin):
	#form = autocomplete_light.modelform_factory(ElsterMeterTrack)
	#fields = []
	actions = [export_elster_meter_track_csv]

	fieldsets = [ 
		(None,              {'fields': [('elster_serial_number', 'meter_style','meter_barcode','manufacture_date',), 
					('rma_number','rma_create_date','rma_receive_date','rma_complete_date',),
					('defect','complaint',),
					('finding','action_taken',),]})
		] 
	list_display = ('elster_serial_number', 'meter_barcode', 'rma_number','meter_style_description','complaint','rma_create_date','rma_complete_date','defect_id_desc',)
	search_fields = ['elster_serial_number', 'rma_number', 'meter_barcode',]
	list_filter = [ElsterMeterRmaCreateListFilter, ElsterMeterRmaCompleteListFilter,'defect__description', 'meter_style',]

class CustomerMeterTrackAdmin(admin.ModelAdmin):
	fieldsets = [ 
		(None,              {'fields': [('elster_meter_serial_number', 'meter_type','meter_barcode',), 
					('order_date','set_date','failure_date',),
					('reason_for_removal','customer_defined_failure_code','failure_detail',),
					('ship_date', 'tracking_number',),
					('exposure','service_status','original_order_information',),
					('longitude','latitude','address'),]})
		] 
	search_fields = ['meter_barcode','failure_date','customer_defined_failure_code', 'tracking_number','original_order_information',]

class ElsterRmaDefectAdmin(admin.ModelAdmin):
	fields=[]
	list_display = ('defect_id', 'description','failure')
	
class ElsterMeterTypeAdmin(admin.ModelAdmin):
	fields=[]
	list_display = ('style','category','description')
	
class AccountAdmin(admin.ModelAdmin):
	fields=[]
	
class ElsterMeterCountAdmin(admin.ModelAdmin):
	fields=[]
	
admin.site.register(ElsterMeterTrack, ElsterMeterTrackAdmin)
admin.site.register(CustomerMeterTrack, CustomerMeterTrackAdmin)
admin.site.register(ElsterMeterType, ElsterMeterTypeAdmin)
admin.site.register(ElsterRmaDefect, ElsterRmaDefectAdmin)
admin.site.register(Account,AccountAdmin)
admin.site.register(ElsterMeterCount, ElsterMeterCountAdmin)