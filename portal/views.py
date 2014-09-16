from django.template import RequestContext
from django.shortcuts import render, get_object_or_404, render_to_response, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django_tables2   import RequestConfig
from django.core.exceptions import ObjectDoesNotExist
import settings
from portal.models import *
from portal.tables import *
from portal.forms import *
from django import forms
import calendar
from django.contrib import messages

import csv
from django.utils.encoding import smart_str
from django.http import HttpResponse

ITEMS_PER_PAGE = settings.ITEMS_PER_PAGE

def index(request):
	return render_to_response("index.html", RequestContext(request))
	
def contact(request):
	return render(request,'contact.html')

@login_required()
def elster_meter_q_list(request):
	template = 'portal/elster_meter_q_list.html'
	# Retrieve 
	meters = ElsterMeterTrack.objects.all().order_by('rma_receive_date')
	table = ElsterMeterTrackTable(meters)
	RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
	return render(request, template, {'table': table})

@login_required()
def cust_meter_q_list(request):
	# Retrieve 
	template = 'portal/cust_meter_q_list.html'	
	meters = CustomerMeterTrack.objects.all().order_by('failure_date')
	table = CustomerMeterTrackTable(meters)
	RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
	return render(request, template, {'table': table})

def __top_five_all_time(request, data):
	now = datetime.datetime.now()
	this_year = now.year
	this_month = now.month
	all_time_defects = {}
	
	# Top defects 'all time'
	for defect in ElsterRmaDefect.objects.all():
		all_time_defects[defect] = ElsterMeterTrack.objects.filter(rma_complete_date__isnull=False,defect=defect).count()
	try:
		no_eval_defect = ElsterRmaDefect.objects.get(defect_id=397)
		del all_time_defects[no_eval_defect] # this one doesn't count in the total
	except ObjectDoesNotExist:
		pass
		
		
	top_five_all_time = sorted(all_time_defects,key=all_time_defects.get,reverse=True)[:5]
	
	# Collect counts for all-time-top-5 by year
	from_year = this_year
	try:
		d = ElsterMeterTrack.objects.all().order_by('rma_create_date').first().rma_create_date
	except ObjectDoesNotExist:
		d = None
	if d:
		from_year = d.year
	defects_through_years = []
	
	# Get the counts for each of the top five for each year
	for d in top_five_all_time:
		def_for_year = {}
		def_for_year['defect']=d.description
		years=[]
		total_count = 0
		for y in range(from_year, this_year+1):
			year={}
			year['year'] = y
			count = ElsterMeterTrack.objects.filter(
				rma_create_date__gte=datetime.date(y,1,1),
				rma_create_date__lte=datetime.date(y,12,31),
				rma_complete_date__isnull=False,
				defect=d).count()
			years.append(year)
			year['count'] = count
			total_count += count
		def_for_year['years']=years
		def_for_year['total_count']=total_count
		defects_through_years.append(def_for_year)
	
	# Now get the totals for all defects BY YEAR
	totals_by_year = ['Top 5 Totals']
	grand_total = 0
	year_list = []
	for y in range(from_year, this_year+1):
		year_list.append(y)
		total = 0
		for d in top_five_all_time: 
			count = ElsterMeterTrack.objects.filter(
					rma_create_date__gte=datetime.date(y,1,1),
					rma_create_date__lte=datetime.date(y,12,31),
					rma_complete_date__isnull=False,
					defect=d).count()
			total += count
		totals_by_year.append(total)
		grand_total += total
	totals_by_year.append(grand_total)
	
	# Now get the totals for all OTHER defects BY YEAR
	totals_others_by_year = ['All Others']
	grand_total = 0
	for y in range(from_year, this_year+1):
		total = ElsterMeterTrack.objects.filter(
				rma_create_date__gte=datetime.date(y,1,1),
				rma_create_date__lte=datetime.date(y,12,31),
				rma_complete_date__isnull=False).exclude(defect__in=top_five_all_time).count()
		totals_others_by_year.append(total)
		grand_total += total
	totals_others_by_year.append(grand_total)

	grand_totals_by_year = ['Grand Total']
	for i in xrange(1, len(totals_by_year)):
		grand_totals_by_year.append(totals_by_year[i] + totals_others_by_year[i])
		
	# Populate data dictionary
	data['defects_through_years']=defects_through_years
	data['all_time_defects']=all_time_defects
	data['top_five_all_time']=top_five_all_time
	data['totals_by_year']=totals_by_year
	data['year_list']=year_list
	data['totals_others_by_year']=totals_others_by_year
	data['grand_totals_by_year']=grand_totals_by_year

def __this_year_top_five(request, data):
	'''
		Now Build the same information but just for the months of present year to-date
		this_year
		month
	'''
	now = datetime.datetime.now()
	this_year = now.year
	this_month = now.month
	all_time_defects = {}
	
	# Top defects 'all time'
	for defect in ElsterRmaDefect.objects.all():
		all_time_defects[defect] = ElsterMeterTrack.objects.filter(
			rma_complete_date__isnull=False,
			rma_create_date__gte=datetime.date(this_year,1,1),
			defect=defect).count()
			
	'''  They eliminate defect_id 397 for all time but apparently not this year ??
	try:
		no_eval_defect = ElsterRmaDefect.objects.get(defect_id=397)
		del all_time_defects[no_eval_defect] # this one doesn't count in the total
	except ObjectNotFound:
		pass
	'''
	top_five_this_year = sorted(all_time_defects,key=all_time_defects.get,reverse=True)[:5]

	defects_through_months = []
	# Get the counts for each of the top five for each month
	for d in top_five_this_year:
		def_for_month = {}
		def_for_month['defect']=d.description
		months=[]
		total_count = 0
		for m in range(1, now.month+1):
			month = {}
			month['month'] = datetime.date(this_year,m,1).strftime("%b")
			count = ElsterMeterTrack.objects.filter(
				rma_create_date__gte=datetime.date(this_year,m,1),
				rma_create_date__lte=datetime.date(this_year,m,calendar.monthrange(this_year,m)[1]),
				rma_complete_date__isnull=False,
				defect=d).count()
			months.append(month)
			month['count'] = count
			total_count += count
		def_for_month['months']=months
		def_for_month['total_count']=total_count
		defects_through_months.append(def_for_month)
		
	# Now get the totals for all defects BY MONTH
	totals_by_month = ['Top 5 Totals for %d'%this_year]
	grand_total = 0
	month_list = []
	for m in range(1, now.month+1):
		month_list.append(datetime.date(this_year,m,1).strftime("%b"))
		total = 0
		for d in top_five_this_year: 
			count = ElsterMeterTrack.objects.filter(
					rma_create_date__gte=datetime.date(this_year,m,1),
					rma_create_date__lte=datetime.date(this_year,m,calendar.monthrange(this_year,m)[1]),
					rma_complete_date__isnull=False,
					defect=d).count()
			total += count
		totals_by_month.append(total)
		grand_total += total
	totals_by_month.append(grand_total)
	
	# Now get the totals for all OTHER defects BY MONTH
	totals_others_by_month = ['All Others']
	grand_total = 0
	for m in range(1, this_month+1):
		total = ElsterMeterTrack.objects.filter(
				rma_create_date__gte=datetime.date(this_year,m,1),
				rma_create_date__lte=datetime.date(this_year,m,calendar.monthrange(this_year,m)[1]),
				rma_complete_date__isnull=False).exclude(defect__in=top_five_this_year).count()
		totals_others_by_month.append(total)
		grand_total += total
	totals_others_by_month.append(grand_total)

	grand_totals_by_month = ['Grand Total']
	for i in xrange(1, len(totals_by_month)):
		grand_totals_by_month.append(totals_by_month[i] + totals_others_by_month[i])
	
	
	data['top_five_this_year']=top_five_this_year
	data['this_year']=this_year
	data['defects_through_months']=defects_through_months
	data['totals_by_month']=totals_by_month
	data['month_list']=month_list
	data['totals_others_by_month']=totals_others_by_month
	data['grand_totals_by_month']=grand_totals_by_month
	
@login_required()
def elster_meter_top_five(request):
	template = 'portal/elster_top_five.html'

	data = {} # Table data will go into this dictionary
	__top_five_all_time(request, data)
	__this_year_top_five(request,data)

	return render(request, template, data)

@login_required
def top_five_all_time_to_csv(request):
	template = 'portal/elster_top_five.html'
	data = {}
	__top_five_all_time(request, data)
	
	# Create the HttpResponse object with the appropriate CSV header.
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="elster_top_5_all_time.csv"'
	
	writer = csv.writer(response)
		
	try:
		response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
		#header
		header = [smart_str(u'Defect Description')]
		for year in data['year_list']:
			header.append(smart_str(year))
		header.append(smart_str(u'Total'))
		writer.writerow(header)
		
		for defect in data['defects_through_years']:
			row = [smart_str(defect['defect'])]
			for year_item in defect['years']:
				row.append(smart_str(year_item['count']))
			row.append(smart_str(defect['total_count']))
			writer.writerow(row)
	except Exception as err:
		messages.error(request, 'Error %s building download'%err )
		return HttpResponseRedirect('/')
			
	return response
	
@login_required
def top_five_monthly_to_csv(request):
	template = 'portal/elster_top_five.html'
	data = {}
	__this_year_top_five(request, data)

	# Create the HttpResponse object with the appropriate CSV header.
	response = HttpResponse(content_type='text/csv')
	response['Content-Disposition'] = 'attachment; filename="elster_top_5_monthly.csv"'
	
	writer = csv.writer(response)
		
	try:
		# do some stuff
		response.write(u'\ufeff'.encode('utf8')) # BOM (optional...Excel needs it to open UTF-8 file properly)
		#header
		header = [smart_str(u'Defect Description')]
		for month in data['month_list']:
			header.append(smart_str(month))
		header.append(smart_str(u'Total'))
		writer.writerow(header)
		
		for defect in data['defects_through_months']:
			row = [smart_str(defect['defect'])]
			for month_item in defect['months']:
				row.append(smart_str(month_item['count']))
			row.append(smart_str(defect['total_count']))
			writer.writerow(row)
	except Exception as err:
		messages.error(request, 'Error %s building download'%err )
		return HttpResponseRedirect('/')
			
	return response
	
@login_required()
def choose_elster_rma(request):
	template = 'portal/choose_elster_rma.html'
	redirect_template = 'portal/elster_rma'
	
	user = request.user

	form = ElsterMeterTrackSearchForm(request.POST or None)
	data['form'] = form
	if request.method == 'POST': # If the form has been submitted...
		if form.is_valid(): # All validation rules pass

			start_date = None
			period = None
			rma_number = None
			start_date = form.cleaned_data['start_date']

			if start_date:
				start_date = str(start_date)
			period = form.cleaned_data['period']
			rma_number = form.cleaned_data['rma_number']
			#if period:
			#	period = str(period[0])

			return HttpResponseRedirect('%s/%s/%02d' % (redirect_template, start_date, int(period))) # Redirect after POST
		else:
			return render(request, template, data)
	else:
		form = ElsterMeterTrackSearchForm() # An unbound form
		data['form'] = form

	return render(request, template, data)

@login_required()
def elster_rma_serial(request, serial):
	#template = 'portal/elster_rma_serial.html'
	template = 'portal/elster_meter_q_list.html'
	try:
		rma = ElsterMeterTrack.objects.filter(elster_serial_number=serial)
	except Exception as err:
		messages.error(request, 'Error %s looking up serial: %s' %(str(err),serial))
		return HttpResponseRedirect('/')
	if  len(rma) == 0:
		messages.error(request, 'No records for elster serial#: %s' %serial, fail_silently=True)
		return HttpResponseRedirect('/')
		
	'''
	form = EnergyUsageForm()
	form.fields["start_date"].initial = datetime.date(int(year),int(month),int(day))
	form.fields["period"].initial = num
	data['form'] = form
	'''
	table = ElsterMeterTrackTable(rma)
	RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
	return render(request, template, {'table': table})
	
@login_required()
def elster_rma(request, rma_number):
	template = 'portal/elster_meter_q_list.html'
	try:
		rma = ElsterMeterTrack.objects.filter(rma_number=rma_number)
	except Exception as err:
		messages.error(request, 'Error %s looking up rma number: %s' %(str(err),rma_number))
		return HttpResponseRedirect('/')
	if  len(rma) == 0:
		messages.error(request, 'No records for elster rma#: %s' %rma_number, fail_silently=True)
		return HttpResponseRedirect('/')
		
	'''
	form = EnergyUsageForm()
	form.fields["start_date"].initial = datetime.date(int(year),int(month),int(day))
	form.fields["period"].initial = num
	data['form'] = form
	'''
	table = ElsterMeterTrackTable(rma)
	RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
	return render(request, template, {'table': table})

@login_required()
def edit_elster_rma(request, id=None):
	form_args = {}
	emt = get_object_or_404(ElsterMeterTrack, pk=id)
	# else create new ElsterMeterTrack...
	if request.POST:
		elster_meter_track_form = ElsterMeterTrackForm(request.POST, instance = emt)
		if elster_meter_track_form.is_valid():
			emt = elster_meter_track_form.save(commit=True)
	else:
		elster_meter_track_form = ElsterMeterTrackForm(instance = emt)
		
	return render_to_response('portal/elster_meter_track.html',
			{
			'elster_meter_track_form': elster_meter_track_form
			},
			context_instance=RequestContext(request)
		)