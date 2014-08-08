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
        (r'^static/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.STATIC_ROOT}),
    )