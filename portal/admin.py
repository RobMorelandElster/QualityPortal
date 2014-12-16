#import autocomplete_light
#autocomplete_light.autodiscover()

from django.contrib import admin

# Register your models here.
from models import *
from forms import ElsterMeterTrackForm

from django import forms
from django.template import RequestContext

from django.forms import TextInput, Textarea, ChoiceField
from django.template import Template, Context
from django.shortcuts import render

from datetime import date

from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse, HttpResponseRedirect

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
			('365', _('in past year')),
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
		if self.value() == '365':
			return queryset.filter(rma_create_date__gte=now-datetime.timedelta(days=365))

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
	error_msgs = []
	error_count = 0
	for obj in queryset:
		try:
			if obj.defect:
				defect_description = obj.defect.description
			else:
				defect_description = 'None'
			writer.writerow([
				smart_str(obj.elster_serial_number),
				smart_str(obj.meter_style.description),
				smart_str(obj.meter_barcode),
				smart_str(obj.manufacture_date),
				smart_str(obj.rma_number),
				smart_str(obj.rma_create_date),
				smart_str(obj.rma_receive_date),
				smart_str(obj.rma_complete_date),
				smart_str(defect_description),
				smart_str(obj.complaint),
				smart_str(obj.finding),
				smart_str(obj.action_taken),
			])
		except Exception as inst:
			error_msgs.append('export Error: %s for record#: %s' % (str(inst), str(obj)))
			error_count += 1
			if (error_count > 20):
				break
			else:
				pass
	if len(error_msgs):
		print '\n'.join(error_msgs)
		modeladmin.message_user(request, 'Error(s) exporting:\n'.join(error_msgs))
	return response
export_elster_meter_track_csv.short_description = u"Export Elster Meters CSV"

class ElsterMeterTrackAdmin(admin.ModelAdmin):
	form = ElsterMeterTrackForm
	actions = [export_elster_meter_track_csv]

	list_display = ('elster_serial_number', 'meter_barcode', 'rma_number','meter_style_description','complaint','rma_create_date','rma_complete_date','defect_id_desc',)
	search_fields = ['elster_serial_number', 'rma_number', 'meter_barcode',]
	list_filter = [ElsterMeterRmaCreateListFilter, ElsterMeterRmaCompleteListFilter,'defect__description', 'meter_style',]

class ShipmentAdmin(admin.ModelAdmin):
	fields=[]
	search_fields = ['reference_id', 'ship_date', 'tracking_number', 'pallet_number',]
	list_display = ('reference_id', 'ship_date', 'tracking_number', 'pallet_number',)

class ChooseShipmentForm(forms.Form):
	_selected_action = forms.CharField(widget=forms.MultipleHiddenInput)
	shipment = forms.ModelChoiceField(queryset=Shipment.objects.all(), required=True)
	
def set_shipment(modeladmin, request, queryset):
	opts = modeladmin.model._meta
	app_label = opts.app_label

	form = None
	if 'cancel' in request.POST:
		modeladmin.message_user(request, 'Canceled link shipment')
		return
	elif 'post' in request.POST:
		# update shipment
		form = ChooseShipmentForm(request.POST)
		if form.is_valid():
			shipment = form.cleaned_data['shipment']
			for record in queryset:
				record.shipment = shipment
				record.save()
			modeladmin.message_user(request, "Successuflly updated %d records"% queryset.count(), )
			return HttpResponseRedirect(request.get_full_path())

	if not form:
		form = ChooseShipmentForm(initial={'_selected_action': request.POST.getlist(admin.ACTION_CHECKBOX_NAME)})

	context = {
		'queryset': queryset,
		'records': queryset,
		'form': form,
		'path':request.get_full_path(),
		'app_label': app_label,
	}
	return render(request, 'admin/set_shipment.html', context)
set_shipment.short_description = 'Set shipment information'
	
class CustomerMeterTrackAdmin(admin.ModelAdmin):
	search_fields = ['elster_meter_serial_number','meter_barcode','failure_date','rma_number', 'shipment__reference_id',]
	list_display = ['elster_meter_serial_number','meter_barcode', 'failure_date','rma_number','shipment',]
	actions = [set_shipment]
	list_filter = ['shipment','reason_for_removal',]

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
admin.site.register(Shipment, ShipmentAdmin)