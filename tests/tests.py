import django
from django.contrib.auth.models import User
from django.test import TestCase
from django.test.client import RequestFactory

from django.test.client import Client

from portal.models import *
from django.utils import timezone
from datetime import date
from dateutil.relativedelta import relativedelta
from django.core.urlresolvers import reverse
from decimal import Decimal

from django.utils import timezone
from csvimport.models import CSVImportElsterMeterTrack
from django.test.utils import override_settings

@override_settings(DEFAULT_FILE_STORAGE='django.core.files.storage.FileSystemStorage')
class TestPortal(TestCase):
	"""	
	Test the top 5 report 
	"""
	def setUp(self):
		self.factory = RequestFactory()
		self.client = Client()
		django.test.utils.setup_test_environment()
		self.user=User.objects.create_user(
			username='test',
			password='test',
			email='test@email.com')
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
		ElsterMeterTrack.objects.create(
			elster_serial_number='1',
			meter_style=m_type,
			rma_create_date=datetime.date(2013,1,1)+relativedelta(months=1),
			rma_complete_date=datetime.date(2013,1,1)+relativedelta(months=2),
			defect = self.defect_1,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='2',
			meter_style=m_type,
			rma_create_date=datetime.date(2013,1,1)+relativedelta(months=2),
			rma_complete_date=datetime.date(2013,1,1)+relativedelta(months=3),
			defect = self.defect_1,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='3',
			meter_style=m_type,
			rma_create_date=datetime.date(2014,1,1),
			rma_complete_date=datetime.date(2014,1,1)+relativedelta(months=1),
			defect = self.defect_3,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='4',
			meter_style=m_type,
			rma_create_date=datetime.date(2014,1,1)+relativedelta(months=2),
			rma_complete_date=datetime.date(2014,1,1)+relativedelta(months=3),
			defect = self.defect_3,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='5',
			meter_style=m_type,
			rma_create_date=datetime.date(2014,1,1)+relativedelta(months=3),
			rma_complete_date=datetime.date(2014,1,1)+relativedelta(months=4),
			defect = self.defect_5,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='6',
			meter_style=m_type,
			rma_create_date=datetime.date(datetime.date.today().year,1,1)+relativedelta(months=2),
			rma_complete_date=datetime.date(datetime.date.today().year,1,1)+relativedelta(months=3),
			defect = self.defect_3,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='7',
			meter_style=m_type,
			rma_create_date=datetime.date(datetime.date.today().year,1,1)+relativedelta(months=3),
			rma_complete_date=datetime.date(datetime.date.today().year,1,1)+relativedelta(months=4),
			defect = self.defect_5,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='8',
			meter_style=m_type,
			rma_create_date=datetime.date(datetime.date.today().year,1,1)+relativedelta(months=2),
			rma_complete_date=datetime.date(datetime.date.today().year,1,1)+relativedelta(months=3),
			defect = self.defect_1,
			)
		ElsterMeterTrack.objects.create(
			elster_serial_number='9',
			meter_style=m_type,
			rma_create_date=datetime.date(datetime.date.today().year,1,1),
			rma_complete_date=datetime.date(datetime.date.today().year,1,1)+relativedelta(months=1),
			defect = self.defect_3,
			)
			
		#start_datetime = datetime.datetime.today()
		
	def test_deny_anonymous(self):
		response = self.client.get(reverse('elster_top_five'))
		self.assertEquals(response.status_code,302)
		login_successful = self.client.login(username=self.user.username, password='test')
		self.assertTrue(login_successful)
		# Now that the user is logged in we should be able to run the top_five
		response = self.client.get(reverse('elster_top_five'))
		self.assertEquals(response.status_code,200)
		self.client.logout()
		# Now that the user is logged OUT we should NOT be able to run the top_five
		response = self.client.get(reverse('elster_top_five'))
		self.assertEquals(response.status_code,302)
		
	def test_login(self):
		response = self.client.post('/account/login/', {'username': self.user.username, 'password': 'test'})
		self.assertEqual(response.status_code, 200)

	def test_view_context_results(self):
		login_successful = self.client.login(username=self.user.username, password='test')
		self.assertTrue(login_successful)
		# Now that the user is logged in we should be able to run the top_five report
		response = self.client.get(reverse('elster_top_five'))
		self.assertEquals(response.status_code,200)
		
		self.assertEquals(response.context[-1]['totals_by_year'][1],2) # for year 1
		self.assertEquals(response.context[-1]['totals_by_year'][2],3) # for year 2
		
		self.assertEquals(response.context[-1]['top_five_all_time'][0], self.defect_3)
		self.assertEquals(response.context[-1]['top_five_all_time'][1], self.defect_1)
		self.assertEquals(response.context[-1]['top_five_all_time'][2], self.defect_5)
		
		self.assertEquals(response.context[-1]['top_five_this_year'][0], self.defect_3)
		self.assertEquals(response.context[-1]['top_five_this_year'][1], self.defect_1)

	def test_import_elster_csv(self):
		from csvimport.management.commands.elstermetertrackcsvimport import Command
		cmd = Command()
		cmd.setup( uploaded = 'test_files/elster_csv_good.csv', defaults = 'utf-8')
		errors = cmd.run(logid = 1)
		self.assertFalse("Error" in str(errors))
		cmd.setup( uploaded = 'test_files/elster_csv_short.csv', defaults = 'utf-8')
		errors = cmd.run(logid = 2)
		self.assertTrue("Incorrect number of columns 12. Should be 13" in str(errors))
