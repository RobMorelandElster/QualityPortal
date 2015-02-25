from django.template import RequestContext
from django.shortcuts import render, get_object_or_404, render_to_response, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django_tables2   import RequestConfig
from django.db.models import Count
from django.core.exceptions import ObjectDoesNotExist
import settings
from portal.models import *
from portal.tables import *

import autocomplete_light
autocomplete_light.autodiscover()

from portal.forms import *
from django import forms
import calendar
from django.contrib import messages

import traceback
import csv
from django.utils.encoding import smart_str
from django.http import HttpResponse

from urllib2 import urlopen
import json

from .rest_calls import *

ITEMS_PER_PAGE = settings.ITEMS_PER_PAGE

def index(request):
    template = 'index.html'
    data = {}
    
    try:
        data['total_elster_records'] = ElsterMeterTrack.objects.all().count()
        data['total_customer_records'] = CustomerMeterTrack.objects.all().count()
        data['total_outstanding_rma'] = ElsterMeterTrack.objects.filter(rma__complete_date__isnull=True).count()
    except Exception as err:
        print "oops: %s"%err
        messages.error(request, 'Error %s determing totals'%err )
        return HttpResponseRedirect(template)
        
    __elster_defect_trending(request, data)
    __this_year_failure_vs_non(request, data)
    
    return render(request, template, data)

def moving_av(l, n):
    """Take a list, l, and return the average of its last n elements.
    """
    observations = len(l[-n:])
    return sum(l[-n:]) / float(observations)
    
def __elster_defect_trending(request, data):
    new_defects = {}
    t_defects = {}
    # Top defects 'all time'
    try:
        # Find latest defects for the past six months
        one_year = 56 #weeks
        month = 4 #weeks
        
        latest = ElsterMeterTrack.objects.all().order_by('rma__create_date').last()
        if latest:
            last_date = latest.rma.create_date
        else:
            last_date = datetime.datetime.now()
        beginning_date =  last_date - datetime.timedelta(weeks=one_year)
        date_index = beginning_date
        for w in range(month, one_year, month):
            from_date = date_index
            to_date = beginning_date + datetime.timedelta(weeks=w)
            defects = ElsterRmaDefect.objects.filter(
                elstermetertrack__rma__create_date__range=(from_date, to_date), 
                failure=True).annotate(Count('elstermetertrack'))
            for d in defects:
                try:
                    l = new_defects[d]
                    l.append(d.elstermetertrack__count)
                    new_defects[d]=l
                except KeyError:
                    new_defects[d]=[d.elstermetertrack__count]
            date_index = to_date
            
        defect_scores = {}
        for defect, counts in new_defects.iteritems():
            d6_moving_av = moving_av(counts, int(len(new_defects)/4))
            d12_moving_av = moving_av(counts, len(new_defects))
            defect_scores[defect] = ((d6_moving_av - d12_moving_av) / d12_moving_av) * 100 #make it percentage
            
        t_six_months = defect_scores
        for d in t_six_months:
            t_defects[d]=defect_scores[d]
    except ObjectDoesNotExist:
        pass
    data['defect_counts'] = t_defects

def contact(request):
    return render(request,'contact.html')

@login_required()
def elster_meter_q_list(request):
    template = 'portal/elster_meter_q_list.html'
    redirect_template = '/elster_rma_date_range'
    redirect_template_rma = '/elster_rma'
    choose_template = '/choose_elster_rma'
    
    # Retrieve 
    meters = ElsterMeterTrack.objects.all().order_by('rma__create_date')
    rec_count = meters.count()
    table = ElsterMeterTrackTable(meters)
    
    start_date = None
    if rec_count:
        start_date = meters[0].rma.create_date
        
    form = ElsterMeterTrackSearchForm(request.POST or None)
    data = {}
    
    data['form'] = form 
    form.initial={'start_date': start_date, 'rma_number': '',  'search_type': 'date_range' }
    
    if request.method == 'POST': # If the form has been submitted...
        if form.is_valid(): # All validation rules pass

            start_date = None
            end_date = None
            rma_number = None
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            if start_date:
                start_date = str(start_date)
            if end_date:
                end_date = str(end_date)
                
            rma_number = form.cleaned_data['rma_number']
            if len(rma_number):
                return HttpResponseRedirect('%s/%s' % (redirect_template_rma, rma_number)) # Redirect after POST
            else:
                return HttpResponseRedirect('%s/%s/%s' % (redirect_template, start_date, end_date)) # Redirect after POST
        else:
            data['form'] = form
            return render(request, template, data)

    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, template, 
        {'table': table, 
            'drill_down': '', 
            'rec_count':rec_count, 
            'form': form,
            'search_type': 'date_range',
        })

@login_required()
def cust_meter_q_list(request):
    # Retrieve 
    template = 'portal/cust_meter_q_list.html'  
    meters = CustomerMeterTrack.objects.all().order_by('failure_date')
    rec_count=meters.count()
    table = CustomerMeterTrackTable(meters)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, template, {'table': table, 'rec_count': rec_count})

def __top_five_all_time(request, data):
    now = datetime.datetime.now()
    this_year = now.year
    this_month = now.month
    all_time_defects = {}
    
    # Top defects 'all time'
    for defect in ElsterRmaDefect.objects.all():
        all_time_defects[defect] = ElsterMeterTrack.objects.filter(rma__complete_date__isnull=False,defect=defect).count()
    try:
        no_eval_defect = ElsterRmaDefect.objects.get(defect_id=397)
        del all_time_defects[no_eval_defect] # this one doesn't count in the total
    except ObjectDoesNotExist:
        pass
        
        
    top_five_all_time = sorted(all_time_defects,key=all_time_defects.get,reverse=True)[:5]
    
    # Collect counts for all-time-top-5 by year
    from_year = this_year
    try:
        first = ElsterMeterTrack.objects.all().order_by('rma__create_date').first()
        if first:
            d = first.rma.create_date
        else:
            d = None
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
                rma__create_date__gte=datetime.date(y,1,1),
                rma__create_date__lte=datetime.date(y,12,31),
                rma__complete_date__isnull=False,
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
                    rma__create_date__gte=datetime.date(y,1,1),
                    rma__create_date__lte=datetime.date(y,12,31),
                    rma__complete_date__isnull=False,
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
                rma__create_date__gte=datetime.date(y,1,1),
                rma__create_date__lte=datetime.date(y,12,31),
                rma__complete_date__isnull=False).exclude(defect__in=top_five_all_time).count()
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
    try:
        this_year = data['this_year']
        this_month = data['this_month']
    except KeyError:
        now = datetime.datetime.now()
        this_year = now.year
        this_month = now.month
    all_time_defects = {}
    
    # Top defects 'all time'
    for defect in ElsterRmaDefect.objects.all():
        all_time_defects[defect] = ElsterMeterTrack.objects.filter(
            rma__complete_date__isnull=False,
            rma__create_date__gte=datetime.date(this_year,1,1),
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
        for m in range(1, this_month+1):
            month = {}
            month['month'] = datetime.date(this_year,m,1).strftime("%b")
            count = ElsterMeterTrack.objects.filter(
                rma__create_date__gte=datetime.date(this_year,m,1),
                rma__create_date__lte=datetime.date(this_year,m,calendar.monthrange(this_year,m)[1]),
                rma__complete_date__isnull=False,
                defect=d).count()
            months.append(month)
            month['date_str'] = "%d, %d, 1"%(this_year, m-1) # Months are zero based for Javascript Date constructor
            month['count'] = count
            total_count += count
        def_for_month['months']=months
        def_for_month['total_count']=total_count
        defects_through_months.append(def_for_month)
        
    # Now get the totals for all defects BY MONTH
    totals_by_month = ['Top 5 Totals for %d'%this_year]
    grand_total = 0
    month_list = []
    for m in range(1, this_month+1):
        month_list.append(datetime.date(this_year,m,1).strftime("%b"))
        total = 0
        for d in top_five_this_year: 
            count = ElsterMeterTrack.objects.filter(
                    rma__create_date__gte=datetime.date(this_year,m,1),
                    rma__create_date__lte=datetime.date(this_year,m,calendar.monthrange(this_year,m)[1]),
                    rma__complete_date__isnull=False,
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
                rma__create_date__gte=datetime.date(this_year,m,1),
                rma__create_date__lte=datetime.date(this_year,m,calendar.monthrange(this_year,m)[1]),
                rma__complete_date__isnull=False).exclude(defect__in=top_five_this_year).count()
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
    if not ElsterMeterTrack.objects.filter(rma__create_date__gte=datetime.datetime(datetime.datetime.now().year, 1,1), rma__complete_date__gte=datetime.datetime(datetime.datetime.now().year, 1,1)).count():
        data['this_year'] = datetime.datetime.now().year -1
        data['this_month'] = 12
    __top_five_all_time(request, data)
    __this_year_top_five(request,data)

    return render(request, template, data)
    
@login_required()
def elster_meter_top_five_graph(request):
    template = 'portal/elster_top_five_graph.html'

    data = {} # Table data will go into this dictionary
    if not ElsterMeterTrack.objects.filter(rma__create_date__gte=datetime.datetime(datetime.datetime.now().year, 1,1), rma__complete_date__gte=datetime.datetime(datetime.datetime.now().year, 1,1)).count():
        data['this_year'] = datetime.datetime.now().year -1
        data['this_month'] = 12
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
        return HttpResponseRedirect(template)
            
    return response
    
@login_required
def top_five_monthly_to_csv(request):
    template = 'portal/elster_top_five.html'
    data = {}
    if not ElsterMeterTrack.objects.filter(rma__create_date__gte=datetime.datetime(datetime.datetime.now().year, 1,1), rma__complete_date__gte=datetime.datetime(datetime.datetime.now().year, 1,1)).count():
        data['this_year'] = datetime.datetime.now().year -1
        data['this_month'] = 12
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
        return HttpResponseRedirect(template)
            
    return response

def __handle_search_type_redirect(request, form, data):
    redirect_template_date_range = '/elster_rma_date_range'
    redirect_template_rma = '/elster_rma'
    redirect_template_serial_barcode = '/elster_rma_serial_barcode'
    template = 'portal/choose_elster_rma.html'

    if form.is_valid(): # All validation rules pass
        search_type = form.cleaned_data['search_type']
        if search_type in'rma_number':
            rma_number = form.cleaned_data['rma_number']
            return HttpResponseRedirect('%s/%s' % (redirect_template_rma, rma_number)) # Redirect after POST
        elif search_type in 'date_range':
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            if start_date:
                start_date = str(start_date)
            if end_date:
                end_date = str(end_date)
            return HttpResponseRedirect('%s/%s/%s' % (redirect_template_date_range, start_date, end_date)) # Redirect after POST
        elif search_type in 'record':
            serial_barcode = form.cleaned_data['meter_track_record']
            if serial_barcode == None:
                messages.error(request, 'Serial/Barcode required for search')
            elif len(serial_barcode) == 0 :
                messages.error(request, 'Serial/Barcode required for search')
            elif len(serial_barcode.split('/')) == 1 :
                return HttpResponseRedirect('%s/%s' % (redirect_template_serial_barcode, serial_barcode.split('/')[0])) # Redirect after POST
            elif len(serial_barcode.split('/')) == 2 :
                return HttpResponseRedirect('%s/%s/%s' % (redirect_template_serial_barcode, serial_barcode.split('/')[0], serial_barcode.split('/')[1])) # Redirect after POST
    form.initial={ 'search_type': 'record' }
    data['form'] = form
    return render(request, template, data)
            
@login_required()
def choose_elster_rma(request):
    template = 'portal/choose_elster_rma.html'
    redirect_template = '/elster_rma_date_range'
    redirect_template_rma = '/elster_rma'
    redirect_template_serial_barcode = '/elster_rma_serial_barcode'
    form = ElsterMeterTrackSearchForm(request.POST or None)
    data = {}
    data['form'] = form

    if request.method == 'POST': # If the form has been submitted...
        response = __handle_search_type_redirect(request, form, data)
        return response
    else:
        data['search_type']='record'
        form = ElsterMeterTrackSearchForm() # An unbound form
        form.initial={ 'search_type': 'record' }
    data['form'] = form
    return render(request, template, data)
    
@login_required()
def elster_rma_date_range(request, byear, bmonth, bday, eyear, emonth, eday):
    template = 'portal/elster_meter_q_list.html'
    from_to_range_str = 'range %s-%s-%s to: %s-%s-%s'%(byear, bmonth, bday, eyear, emonth, eday)
    from_date = datetime.date(int(byear),int(bmonth),int(bday))
    to_date = datetime.date(int(eyear),int(emonth),int(eday))
    redirect_template = '/elster_rma_date_range'
    redirect_template_rma = '/elster_rma'
    choose_template = '/choose_elster_rma'
    
    form = ElsterMeterTrackSearchForm(request.POST or None)
    data = {}
    data['form'] = form
    form.initial={'start_date': from_date, 'end_date': to_date, 'search_type': 'date_range'}

    if request.method == 'POST': # If the form has been submitted...
        response = __handle_search_type_redirect(request, form, data)
        return response
    else:
        try:
            rma = ElsterMeterTrack.objects.filter(rma__create_date__gte=from_date, rma__create_date__lte=to_date).order_by('rma__create_date')
            rec_count = rma.count()
        except Exception as err:
            messages.error(request, 'Error %s searching for Elster Meter Tracks %s' %(str(err), from_to_range_str))
            return HttpResponseRedirect(choose_template)
        if  len(rma) == 0:
            messages.error(request, 'No records for elster meter tracks from create date:%s to:%s' %(from_date, to_date), fail_silently=True)
            return HttpResponseRedirect(choose_template)
    
    table = ElsterMeterTrackTable(rma)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, template, 
        {'table': table, 
            'drill_down': from_to_range_str, 
            'rec_count':rec_count, 
            'form': form,
            'search_type': 'date_range',
        })
    
@login_required()
def elster_rma(request, rma_number):
    template = 'portal/elster_meter_q_list.html'
    redirect_template = '/elster_rma_date_range'
    redirect_template_rma = '/elster_rma'
    choose_template = '/choose_elster_rma'

    form = ElsterMeterTrackSearchForm(request.POST or None)
    data = {}
    data['form'] = form
    form.initial={'rma_number': rma_number,'search_type': 'rma_number'}
    
    
    if request.method == 'POST': # If the form has been submitted...
        response = __handle_search_type_redirect(request, form, data)
        return response
    else:
        try:
            rma = ElsterMeterTrack.objects.filter(rma__number__startswith=rma_number)
            rec_count = rma.count()
        except Exception as err:
            messages.error(request, 'Error %s looking up rma number: %s' %(str(err),rma_number))
            return HttpResponseRedirect(choose_template)
        if  len(rma) == 0:
            messages.error(request, 'No records for elster rma#: %s' %rma_number, fail_silently=True)
            return HttpResponseRedirect(choose_template)
        
    table = ElsterMeterTrackTable(rma)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, template, 
        {'table': table, 
            'drill_down': 'for RMA %s*'%rma_number, 
            'rec_count':rec_count, 
            'form': form,
            'search_type': 'rma',
        })

@login_required()
def elster_rma_serial_barcode(request, serial, barcode=None):
    template = 'portal/elster_meter_q_list.html'
    redirect_template = '/elster_rma_date_range'
    redirect_template_rma = '/elster_rma'
    choose_template = '/choose_elster_rma'

    form = ElsterMeterTrackSearchForm(request.POST or None)
    data = {}
    data['form'] = form
    if barcode:
        form.initial={'meter_track_record': serial+'/'+barcode, 'search_type': 'record'}
    else:
        form.initial={'meter_track_record': serial, 'search_type': 'record'}
    
    
    if request.method == 'POST': # If the form has been submitted...
        response = __handle_search_type_redirect(request, form, data)
        return response
    else:
        try:
            if barcode:
                rma = ElsterMeterTrack.objects.filter(elster_serial_number=serial, meter_barcode=barcode)
            else:
                rma = ElsterMeterTrack.objects.filter(elster_serial_number=serial)
            rec_count = rma.count()
        except Exception as err:
            messages.error(request, 'Error %s looking up record for: serial#:%s and barcode#:%s' %(str(err),serial,barcode))
            return HttpResponseRedirect(choose_template)
        if  len(rma) == 0:
            messages.error(request, 'No records for for: serial#:%s and barcode#:%s' %(serial, barcode), fail_silently=True)
            return HttpResponseRedirect(choose_template)
        
    table = ElsterMeterTrackTable(rma)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, template, 
        {'table': table, 
            'drill_down': 'for Meter Serial:%s Barcode:%s'%(serial,barcode), 
            'rec_count':rec_count, 
            'form': form,
            'search_type': 'record',
        })

@login_required()
def elster_open_rma(request):
    template = 'portal/elster_meter_q_list.html'
    redirect_template = '/elster_rma_date_range'
    redirect_template_rma = '/elster_open_rma'
    choose_template = '/choose_elster_rma'

    form = ElsterMeterTrackSearchForm(request.POST or None)
    data = {}
    data['form'] = form
    form.initial={'rma_number': None,'start_date': None, 'end_date': None, 'search_type': 'rma_number',}
    
    
    if request.method == 'POST': # If the form has been submitted...
        if form.is_valid(): # All validation rules pass

            start_date = None
            end_date = None
            rma_number = None
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            if start_date:
                start_date = str(start_date)
            if end_date:
                end_date = str(end_date)
                
            rma_number = form.cleaned_data['rma_number']
            if len(rma_number):
                return HttpResponseRedirect('%s/%s' % (redirect_template_rma, rma_number)) # Redirect after POST
            else:
                return HttpResponseRedirect('%s/%s/%s' % (redirect_template, start_date, end_date)) # Redirect after POST
        else:
            data['form'] = form
            return render(request, template, data)
    else:
        try:
            open_rma = ElsterMeterTrack.objects.filter(rma__complete_date__isnull=True)
            rec_count = open_rma.count()
        except Exception as err:
            messages.error(request, 'Error %s looking up rma number: %s' %(str(err),rma_number))
            return HttpResponseRedirect(choose_template)
        if  len(open_rma) == 0:
            messages.error(request, 'No open Elster RMAs', fail_silently=True)
            return HttpResponseRedirect(choose_template)
        
    table = ElsterMeterTrackTable(open_rma)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, template, 
        {'table': table, 
            'drill_down': 'Open RMAs', 
            'rec_count':rec_count, 
            'form': form,
            'search_type': 'rma',
        })
        
@login_required()
def elster_rma_by_defect(request, defect_id):
    template = 'portal/elster_meter_q_list.html'
    redirect_template = '/elster_rma_date_range'
    redirect_template_rma = '/elster_rma_by_defect'
    choose_template = '/choose_elster_rma'

    form = ElsterMeterTrackSearchForm(request.POST or None)
    data = {}
    data['form'] = form
    form.initial={'rma_number': None,'start_date': None, 'end_date': None,   'search_type': 'rma_number',}
    defect_description = ''
    
    
    if request.method == 'POST': # If the form has been submitted...
        if form.is_valid(): # All validation rules pass

            start_date = None
            end_date = None
            rma_number = None
            start_date = form.cleaned_data['start_date']
            end_date = form.cleaned_data['end_date']

            if start_date:
                start_date = str(start_date)
            if end_date:
                end_date = str(end_date)
                
            rma_number = form.cleaned_data['rma_number']
            if len(rma_number):
                return HttpResponseRedirect('%s/%s' % (redirect_template_rma, rma_number)) # Redirect after POST
            else:
                return HttpResponseRedirect('%s/%s/%s' % (redirect_template, start_date, end_date)) # Redirect after POST
        else:
            data['form'] = form
            return render(request, template, data)
    else:
        try:
            rma = ElsterMeterTrack.objects.filter(defect__defect_id=defect_id).order_by('-rma__create_date')
            defect_description = ElsterRmaDefect.objects.get(defect_id=defect_id).description
            rec_count = rma.count()
        except Exception as err:
            messages.error(request, 'Error %s looking up rma number: %s' %(str(err),rma_number))
            return HttpResponseRedirect(choose_template)
        if  len(rma) == 0:
            messages.error(request, 'No records for elster defect#: %s' %defect_id, fail_silently=True)
            return HttpResponseRedirect(choose_template)
        
    table = ElsterMeterTrackTable(rma)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, template, 
        {'table': table, 
            'drill_down': 'for %s'%defect_description, 
            'rec_count':rec_count, 
            'form': form,
            'search_type': 'rma',
        })


def is_elster_user(user):
    return user.groups.filter(name='Elster')

def is_customer_user(user):
    return user.groups.filter(name='Customer')

@login_required()
def edit_elster_rma(request, id=None):
    template = 'portal/elster_meter_track.html'
    form_args = {}
    emt = get_object_or_404(ElsterMeterTrack, pk=id)
    # else create new ElsterMeterTrack...
    if request.POST:
            elster_meter_track_form = ElsterMeterTrackForm(request.POST, instance = emt)
            if elster_meter_track_form.is_valid():
                if is_elster_user(request.user):
                    emt = elster_meter_track_form.save(commit=True)
                    messages.info(request, 'Record updated')
                else:
                    messages.error(request, 'User: %s is not authorized to update Elster RMA Records' %request.user, fail_silently=False)
    else:
        elster_meter_track_form = ElsterMeterTrackForm(instance = emt)
        
    return render_to_response(template,
            {

            'elster_meter_track_form': elster_meter_track_form
            },
            context_instance=RequestContext(request)
        )

def __this_year_failure_vs_non(request, data):
    '''
        Determine the count of failure vs. non-failure 
    '''
    template = 'index.html'
    now = datetime.datetime.now()
    data['this_year'] = now.year
    
    
    try:
        try:
            data['first_defect_year'] = ElsterMeterTrack.objects.all().order_by('rma__create_date').first().rma.create_date.year
        except:
            data['first_defect_year'] = now.year
            
        try:
            data['devices_in_service'] = ElsterMeterCount.objects.all().last().meter_count
        except:
            data['devices_in_service'] = 0

        failure_defects = ElsterRmaDefect.objects.filter(failure=True)
        non_failure_defects = ElsterRmaDefect.objects.filter(failure=False)
        data['non_failure_defect_list'] = [nf.description for nf in non_failure_defects]
        
        data['all_time_failure_count'] = ElsterMeterTrack.objects.filter(
                rma__complete_date__isnull=False,
                rma__complete_date__gte=datetime.date(data['first_defect_year'],1,1),
                defect__in=failure_defects).count()
        data['customer_all_time_failure_count'] = CustomerMeterTrack.objects.all().count()
        
        data['this_year_failure_count'] = ElsterMeterTrack.objects.filter(
                rma__complete_date__isnull=False,
                rma__complete_date__gte=datetime.date(data['this_year'],1,1),
                defect__in=failure_defects).count()
        data['customer_this_year_failure_count'] = CustomerMeterTrack.objects.filter(
                failure_date__gte=datetime.date(data['this_year'],1,1)).count()

        data['all_time_non_failure_count'] = ElsterMeterTrack.objects.filter(
                rma__complete_date__isnull=False,
                rma__complete_date__gte=datetime.date(data['first_defect_year'],1,1),
                defect__in=non_failure_defects).count()

        data['this_year_non_failure_count'] = ElsterMeterTrack.objects.filter(
                rma__complete_date__isnull=False,
                rma__complete_date__gte=datetime.date(data['this_year'],1,1),
                defect__in=non_failure_defects).count()
        last = ElsterMeterTrack.objects.filter( rma__complete_date__isnull=False).order_by('rma__complete_date').last()
        up_to = datetime.datetime.now()
        if last:
            if last.rma:
                if last.rma.complete_date:
                    up_to = last.rma.complete_date
        data['up_to'] = up_to
        device_count = 0
        mco = ElsterMeterCount.objects.filter().order_by('as_of_date').last()
        if mco:
            device_count = mco.meter_count
        data['device_count'] = device_count
    except Exception as err:
        print "oops: %s"%err
        messages.error(request, 'Error %s determing defect counts this year'%err )
        return HttpResponseRedirect(template)
    
@login_required()
def data_reports(request):
    template = 'data_reports.html'
    data = {}
    data['reports'] = DataReport.objects.all()
    return render(request, template, data)
    
@login_required()
def run_one_report(request, report_id):    
    redirect_template = '/'
    template = 'data_reports_display.html'
    data = {}
    try:
        report = DataReport.objects.get(pk=report_id)
        print("Getting Report {}".format(report))
        response=urlopen("{}.json".format(report.link))
        result = response.read()
        if len(result):
        	data = json.loads(result)
        	data['report'] = report
        else:
        	messages.error(request, 'No Data from report URL')
        	return HttpResponseRedirect(redirect_template)
    except Exception as err:
    	print "oops: %s"%err
        messages.error(request, 'Error %s rendering report'%err )
        return HttpResponseRedirect(redirect_template)
    return render(request, template, data)