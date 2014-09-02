from django.conf.urls import patterns, include, url
import settings
from portal import views

from django.contrib import admin
admin.autodiscover()

urlpatterns = patterns('',
    # Examples:
    # url(r'^$', 'portal.views.home', name='home'),
    # url(r'^blog/', include('blog.urls')),

    url(r'^admin/', include(admin.site.urls)),
    url(r'^$', views.index, name='index'),
    url(r'^contact/', views.contact, name='contact_us'),
    
    url(r'^account/login', include('allauth.urls'), name='login'),
    url(r'^account/', include('allauth.urls')),

)

urlpatterns += patterns('',
	# forms and lists
	url(r'^elster_qportal/$', views.elster_meter_q_list, name='elster_meter_q_list'),
	url(r'^cust_qportal/$', views.cust_meter_q_list, name='cust_meter_q_list'),
	url(r'^elster_top_five/$', views.elster_meter_top_five, name='elster_top_five'),
	url(r'^top_five_all_time_to_csv/$', views.top_five_all_time_to_csv, name='top_five_all_time_to_csv'),
	url(r'^top_five_monthly_to_csv/$', views.top_five_monthly_to_csv, name='top_five_monthly_to_csv'),

)
    
urlpatterns += patterns('',
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)

urlpatterns += patterns('',
    url(r'^captcha/', include('captcha.urls')),
)