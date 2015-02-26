from django.conf.urls import patterns, include, url
import settings
from portal import views

import autocomplete_light
# import every app/autocomplete_light_registry.py
autocomplete_light.autodiscover()

import admin
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
	url(r'^elster_top_five_graph/$', views.elster_meter_top_five_graph, name='elster_top_five_graph'),
	url(r'^top_five_all_time_to_csv/$', views.top_five_all_time_to_csv, name='top_five_all_time_to_csv'),
	url(r'^top_five_monthly_to_csv/$', views.top_five_monthly_to_csv, name='top_five_monthly_to_csv'),
	url(r'^elster_rma/(?P<rma_number>\S+)/$', 'portal.views.elster_rma', name='elster_rma'),
	url(r'^elster_rma_by_defect/(?P<defect_id>\S+)/$', 'portal.views.elster_rma_by_defect', name='elster_rma_by_defect'),
	url(r'^elster_open_rma/$', 'portal.views.elster_open_rma', name='elster_open_rma'),
	url(r'^elster_rma_date_range/(?P<byear>\d{4})-(?P<bmonth>\d{2})-(?P<bday>\d{2})/(?P<eyear>\d{4})-(?P<emonth>\d{2})-(?P<eday>\d{2})/$', 'portal.views.elster_rma_date_range', name='elster_rma_date_range'),
	url(r'^elster_rma_serial_barcode/(?P<serial>\S+)/(?P<barcode>\S+)/$', 'portal.views.elster_rma_serial_barcode', name='elster_rma_serial_barcode'),
	url(r'^elster_rma_serial_barcode/(?P<serial>\S+)/$', 'portal.views.elster_rma_serial_barcode', name='elster_rma_serial_barcode'),
	url(r'^elster_rma_edit/(?P<id>\d+)?$', views.edit_elster_rma, name='edit_elster_rma'),
	url(r'^choose_elster_rma/$', 'portal.views.choose_elster_rma', name='choose_elster_rma'),
	url(r'^data_reports/$', 'portal.views.data_reports', name='data_reports'),
	url(r'^run_one_report/(?P<report_id>\S+)/$', 'portal.views.run_one_report', name='run_one_report'),
)
	
urlpatterns += patterns('',
	(r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
)

urlpatterns += patterns('',
    url(r'^autocomplete/', include('autocomplete_light.urls')),
)

from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'groups', views.GroupViewSet)
router.register(r'meter_count', views.ElsterMeterCountViewSet)
router.register(r'defect_types', views.ElsterRmaDefectViewSet)
router.register(r'elster_rmas', views.ElsterMeterTrackViewSet)
router.register(r'shipment', views.ShipmentViewSet)
router.register(r'rma', views.ElsterRmaViewSet)


# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browsable API.
urlpatterns += patterns('',
    url(r'^', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^customer_csv_import_file/$', views.customer_csv_import_file),
    url(r'^elster_csv_import_file/$', views.elster_csv_import_file),
)