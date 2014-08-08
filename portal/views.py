from django.template import RequestContext
from django.shortcuts import render, get_object_or_404, render_to_response
from django.contrib.auth.decorators import login_required
from django_tables2   import RequestConfig
import settings
from portal.models import *
from portal.tables import *
from portal.forms import *
from django import forms

ITEMS_PER_PAGE = settings.ITEMS_PER_PAGE

def index(request):
	return render_to_response("index.html", RequestContext(request))
	
def contact(request):
	return render(request,'contact.html')

@login_required()
def elster_meter_q_list(request):
    # Retrieve 
    meters = ElsterMeterTrack.objects.all().order_by('rma_receive_date')
    table = ElsterMeterTrackTable(meters)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, 'portal/elster_meter_q_list.html', {'table': table})

@login_required()
def cust_meter_q_list(request):
    # Retrieve 
    meters = CustomerMeterTrack.objects.all().order_by('failure_date')
    table = CustomerMeterTrackTable(meters)
    RequestConfig(request,paginate={"per_page": ITEMS_PER_PAGE}).configure(table)
    return render(request, 'portal/cust_meter_q_list.html', {'table': table})