from django.template import RequestContext
from django.shortcuts import render, get_object_or_404, render_to_response
from portal import models

def index(request):
	return render_to_response("index.html", RequestContext(request))
	
def contact(request):
	return render(request,'contact.html')