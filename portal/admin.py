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

#class MeterInstallListFilter(SimpleListFilter):
	# Human-readable title which will be displayed in the
	# right admin sidebar just above the filter options.
#	title = _('install date')

	# Parameter for the filter that will be used in the URL query.
#	parameter_name = 'install_date'

#	def lookups(self, request, model_admin):
#		"""
#		Returns a list of tuples. The first element in each
#		tuple is the coded value for the option that will
#		appear in the URL query. The second element is the
#		human-readable name for the option that will appear
#		in the right sidebar.
#		"""
#		return (
#			('1', _('in past day')),
#			('3', _('in past 3 days')),
#			('7', _('in past week')),
#			('30', _('in past month')),
#		)

#	def queryset(self, request, queryset):
#		"""
#		Returns the filtered queryset based on the value
#		provided in the query string and retrievable via
#		`self.value()`.
#		"""
#		now = timezone.now()
		
#		if self.value() == '1':
#			return queryset.filter(install_date__gte=now-datetime.timedelta(days=1))
#		if self.value() == '3':
#			return queryset.filter(install_date__gte=now-datetime.timedelta(days=3))
#		if self.value() == '7':
#			return queryset.filter(install_date__gte=now-datetime.timedelta(days=7))
#		if self.value() == '30':
#			return queryset.filter(install_date__gte=now-datetime.timedelta(days=30))


"""def export_meters_csv(modeladmin, request, queryset):
	response = HttpResponse(mimetype='text/csv')
	response['Content-Disposition'] = 'attachment; filename=meters.csv'
	writer = csv.writer(response, csv.excel)
	response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
	writer.writerow([
		smart_str(u'name'), 
		smart_str(u'meter_type'),
		smart_str(u'profile'), 
		smart_str(u'premise'), 
		smart_str(u'install_date'),
		smart_str(u'last_register_read_datetime'),
		smart_str(u'calendar'), 
		smart_str(u'special_identifier'), 
		smart_str(u'account_owner'),
		])
	for obj in queryset:
		writer.writerow([
			smart_str(obj.name),
			smart_str(obj.meter_type.name),
			smart_str(obj.profile.name),
			smart_str(obj.premise.name),
			smart_str(obj.install_date),
			smart_str(obj.last_register_read_datetime),
			smart_str(obj.calendar.name),
			smart_str(obj.special_identifier),
			smart_str(obj.account_owner),
		])
	return response
export_meters_csv.short_description = u"Export Meters CSV"
"""

class ElsterMeterTrackAdmin(admin.ModelAdmin):
	#form = autocomplete_light.modelform_factory(ElsterMeterTrack)
	fields = []
	#list_display = ('manufacture_number',)
	search_fields = ['manufacture_number', 'manufacture_date', 'defect_code',]
	#list_filter = [MeterInstallListFilter, 'active']

class CustomerMeterTrackAdmin(admin.ModelAdmin):
	fields = []
	search_fields = ['number','order_date','failure_date','system_failure_code','customer_failure_code',]

admin.site.register(ElsterMeterTrack, ElsterMeterTrackAdmin)
admin.site.register(CustomerMeterTrack, CustomerMeterTrackAdmin)
