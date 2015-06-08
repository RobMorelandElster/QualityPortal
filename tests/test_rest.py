import django
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from django.test.client import Client

from portal.models import *
from portal.views import ElsterMeterCountViewSet
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.urlresolvers import reverse

from django.utils import timezone
from django.test.utils import override_settings

from rest_framework.test import APIRequestFactory
from rest_framework.test import APIClient
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class TestRest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.client = Client()
        django.test.utils.setup_test_environment()
        self.user=User.objects.create_user(
            username='test_rest',
            password='secret',
            email='test_rest@email.com')
        self.user.is_staff=True
        self.user.save()
        m_type = ElsterMeterType.objects.create(
            style='ZF-style1',)
        self.defect_1 = ElsterRmaDefect.objects.create(
            defect_id=1,
            description = 'd_1',)
        self.defect_2 = ElsterRmaDefect.objects.create(
            defect_id=2,
            description = 'd_2',)
        self.defect_3 = ElsterRmaDefect.objects.create(
            defect_id=3,
            description = 'd_3',)
        self.defect_4 = ElsterRmaDefect.objects.create(
            defect_id=4,
            description = 'd_4',)
        self.defect_5 = ElsterRmaDefect.objects.create(
            defect_id=5,
            description = 'd_5',)


    def test_meter_count(self):
        '''client = APIClient()
        user = User.objects.get(username='test_rest')
        client.force_authenticate(user=user)
        
        factory = APIRequestFactory()
        data = {
            "meter_count": 100, 
            "as_of_date": '2013-01-01'
        }
        request = factory.post('/meter_count/', data, format='json')
        print "request is: {}".format(request)
        view = ElsterMeterCountViewSet.as_view({'get': 'list'})
        response = view(request)
        print "post response is: {}".format(response)
        
        response = client.get('/meter_count/')
        
        print "test_meter response is: {}".format(response)
        print "response data is: {}".format(response.data)
        client.logout()
        '''
        pass
        
