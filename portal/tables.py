import django_tables2 as tables
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
import itertools
from portal.models import *

counter = itertools.count()

class DivWrappedColumn(tables.Column):

    def __init__(self, classname=None, *args, **kwargs):
        self.classname=classname
        super(DivWrappedColumn, self).__init__(*args, **kwargs)

    def render(self, value):
        return mark_safe("<div class='" + self.classname + "' >" +value+"</div>")

class ElsterMeterTrackTable(tables.Table):
	rma_number = tables.TemplateColumn('<a href="/elster_rma/{{record.rma_number}}">{{record.rma_number}}</a>')
	#name = tables.TemplateColumn('<a href="/inventory/{{record.id}}">{{record.name}}</a>')
	edit = tables.TemplateColumn('<a href="/elster_rma_edit/{{record.id}}"><i class="glyphicon glyphicon-edit"></i></a>',verbose_name = ("Edit"), orderable=False)
	complaint = DivWrappedColumn(classname='long_text_column')
	finding = DivWrappedColumn(classname='long_text_column')
	action_taken = DivWrappedColumn(classname='long_text_column')
	defect = DivWrappedColumn(classname='long_text_column', accessor='defect.description',verbose_name='Root Cause Description')
	#meter_style = tables.Column(accessor='meter_style.meter_style_description', verbose_name='Meter Type')
	class Meta:
		model = ElsterMeterTrack
		# add class="paleblue" to <table> tag
		sequence = ('edit','elster_serial_number',  )
		exclude = ('id','defect_id' )
		attrs = {"class": "table table-striped"}
		template = ('table.html')

class CustomerMeterTrackTable(tables.Table):
	#name = tables.TemplateColumn('<a href="/inventory/{{record.id}}">{{record.name}}</a>')
	#edit = tables.TemplateColumn('<a href="/inventory/part/edit/{{record.id}}"><i class="glyphicon glyphicon-edit"></i></a>',verbose_name = ("Action"), orderable=False)
	class Meta:
		model = CustomerMeterTrack
		# add class="paleblue" to <table> tag
		#sequence = ('manufacture_number', 'edit', )
		exclude = ('id', 'longitude', 'latitude',)
		attrs = {"class": "table table-striped"}
		template = ('table.html')
		

"""
class BinPartTable(tables.Table):
	#part_name = tables.TemplateColumn('<a href="/inventory/{{record.part_type.id}}">{{record.part_type.name}}</a>')
	part_name = tables.Column(accessor = 'part_type.name', verbose_name = ("Part Name"))
	part_supplier = tables.Column(accessor = 'part_type.supplier')
	part_description = tables.Column(accessor = 'part_type.description',orderable=False)
	part_safety_stock = tables.Column(accessor = 'part_type.safety_stock')
	part_cost = tables.Column(accessor = 'part_type.cost')
	count = tables.Column(verbose_name = ('In Stock'))
	class Meta:
		model = Bin
		# add class="paleblue" to <table> tag
		sequence = ('part_name','part_supplier','part_description', 'part_safety_stock', 'count')
		exclude = ('id', 'part_type','name','description','capacity',)
		attrs = {"class": "table table-striped"}
		template = ('table.html')

	def render_part_name(self, record):
	    	return mark_safe('''<a href="/inventory/%s">%s</a>''' % (record.part_type.id, record.part_type.name))
"""