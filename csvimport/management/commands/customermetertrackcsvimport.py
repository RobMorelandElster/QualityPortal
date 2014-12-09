""" 
	This csvimport module needs a lot of work it was roughly hacked from a generic CSV importer
	from www.heliosfoundation.org

	It would be great if someone would refactor this... it breaks DRY all over the place and 
	probably even has code and variables that are never used.  
"""
import os, csv, re, sys
from django.utils import timezone
import datetime, time
from decimal import *
import codecs
import chardet
from ...signals import imported_csv, importing_csv

from django.db import DatabaseError, IntegrityError
from django.core.exceptions import ObjectDoesNotExist
from django.core.management.base import LabelCommand, BaseCommand
from optparse import make_option
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.files.storage import default_storage


from django.conf import settings
CSVIMPORT_LOG = getattr(settings, 'CSVIMPORT_LOG', 'screen')
if CSVIMPORT_LOG == 'logger':
	import logging
	logger = logging.getLogger(__name__)

from portal.models import *

BOOLEAN_TRUE = [1, '1', 'Y', 'Yes', 'yes', 'True', 'true', 'T', 't']
MAX_EXCEPTIONS = 100
DATE_FIELD_SEPARATOR = '-'
NONE_VALUE = 'NULL'
# Note if mappings are manually specified they are of the following form ...
# MAPPINGS = "column1=shared_code,column2=org(Organisation|name),column3=description"
# statements = re.compile(r";[ \t]*$", re.M)

def save_csvimport(props=None, instance=None):
	""" To avoid circular imports do saves here """
	try:
		if not instance:
			from csvimport.models import CSVImport
			csvimp = CSVImport()
		if props:
			for key, value in props.items():
				setattr(csvimp, key, value)
		csvimp.save()
		return csvimp.id
	except:
		# Running as command line
		print '###############################\n'
		for line in instance.loglist:
				print line


class Command(LabelCommand):
	"""
	Parse and import a CSV file to portal.CustomerMeterTrack

	During import existing users will attempt to be matched by "elster_serial_number","meter_barcode","failure_date", 
	Any CustomerMeterTrack entry that already exist will be updated. 
	"""

	option_list = BaseCommand.option_list + (
			   make_option('--file_name', default='customer_meter_track.csv',	help='Please provide the file to import from'),
			   make_option('--charset', default='', help='Force the charset conversion used rather than detect it'))
	help = "Imports a CSV file to the CustomerMeterTrack model"


	def __init__(self):
		""" Set default attributes data types """
		super(Command, self).__init__()
		self.props = {}
		self.debug = False
		self.errors = []
		self.loglist = []
		self.defaults = []
		self.file_name = ''
		self.columns = {
			'ELSTER_METER_SERIAL_NUMBER':0,
			'METER_TYPE':1,
			'METER_BARCODE':2,
			'RMA_NUMBER':3,
			'ORDER_DATE':4,
			'SET_DATE':5,
			'FAILURE_DATE':6,
			'REASON_FOR_REMOVAL':7,
			'CUSTOMER_DEFINED_FAILURE_CODE':8,
			'FAILURE_DETAIL':9,
			'EXPOSURE':10,
			'SHIPMENT_REFERENCE':11,
			'ORIGINAL_ORDER_INFORMATION':12,
			'LONGITUDE':13,
			'LATITUDE':14,
			'ADDRESS':15,
			}

		self.default_user = None
		self.deduplicate = True
		self.csv_reader = []
		self.cloud_file = ''
		self.charset = ''

	def handle_label(self, label, **options):
		""" Handle the circular reference by passing the nested
			save_csvimport function
		"""
		filename = label
		charset = options.get('charset', '')
		org = options.get('org', '')
		# show_traceback = options.get('traceback', True)
		self.setup(org, charset, filename)
		errors = self.run()
		if self.props:
			save_csvimport(self.props, self)
		self.loglist.extend(errors)
		return

	def setup(self, defaults='',
			  uploaded=None, deduplicate=True):
		""" Setup up the attributes for running the import """
		self.deduplicate = deduplicate
		if self.default_user == None:
			try:
				self.default_user = UserProfile.objects.filter(user__first_name__icontains='default')[0]
			except:
				self.default_user = None
		if uploaded:
			if default_storage.exists(uploaded):
				self.cloud_file = default_storage.open(uploaded, 'rb')
				self.csv_reader = csv.reader(self.cloud_file)            
			else:
				raise Exception('File %s not found' % uploaded)
		else:			
			raise Exception('Filename must be supplied')

	def eval_for_null(self, value):
		if value:
			if len(value):
				if value == NONE_VALUE:
					return None
		return value
		
	def run(self, logid=0):
		loglist = []
		indexes = self.csv_reader.next()
		counter = 1 # Count the index line
		exception_count = 0
		if logid:
			csvimportid = logid
		else:
			csvimportid = 0
		if CSVIMPORT_LOG == 'logger':
			logger.info("Import %s %i", ElsterMeterTrack.__name__, counter)

		for raw_row in self.csv_reader:
			counter += 1
			row = []
			# clean it up
			for item in raw_row:
				row.append(item.strip(' "\'\t\r\n'))

			try:
				if (len(row) > len(self.columns)):
					exception_count += 1
					loglist.append('Import Error:Too many columns -- file line %d' % counter)
					if (exception_count > MAX_EXCEPTIONS):
						loglist.append('Exceeded MAX_EXCEPTIONS: %d at file line: %d' % (exception_count,counter))
						break 
					else:
						continue

				elster_meter_serial_number = self.eval_for_null(row[self.columns['ELSTER_METER_SERIAL_NUMBER']])
				if elster_meter_serial_number == None:
					exception_count += 1
					loglist.append('Import Error:Elster Meter Serial Number NULL - skipping record -- file line %d' % counter)
					if (exception_count > MAX_EXCEPTIONS):
						loglist.append('Exceeded MAX_EXCEPTIONS: %d at file line: %d' % (exception_count,counter))
						break 
					else:
						continue
				meter_barcode = self.eval_for_null(row[self.columns['METER_BARCODE']])
				rma_number = self.eval_for_null(row[self.columns['RMA_NUMBER']])
				
				shipment_reference  =self.eval_for_null(row[self.columns['SHIPMENT_REFERENCE']])
				shipment = None
				if shipment_reference:
					try:
						shipment = Shipment.objects.get(reference_id = shipment_reference)
					except ObjectDoesNotExist:
						exception_count += 1
						loglist.append('Invalid shipment reference %s -- file line %d' %(shipment_reference, counter))
						if (exception_count > MAX_EXCEPTIONS):
							loglist.append('Exceeded MAX_EXCEPTIONS: %d at file line: %d' % (exception_count,counter))
							break 
						else:
							continue
						
				# Pull the date fields
				ds = row[self.columns['SET_DATE']]
				set_date = None
				if len(ds)  and ds != 'NULL':
					try:
						ds_split = ds.split(DATE_FIELD_SEPARATOR)
						set_date = datetime.date(int(ds_split[0]),int(ds_split[1]),int(ds_split[2]))
					except IndexError:
						loglist.append('Invalid Set Date %s -- file line %d' %(ds, counter))
						continue
				
				ds = row[self.columns['FAILURE_DATE']]
				failure_date = None
				if len(ds) and ds != 'NULL':
					try:
						ds_split = ds.split(DATE_FIELD_SEPARATOR)
						failure_date = datetime.date(int(ds_split[0]),int(ds_split[1]),int(ds_split[2]))
					except IndexError:
						loglist.append('Invalid Failure Date %s -- file line %d' %(ds, counter))
						continue

				ds = row[self.columns['ORDER_DATE']]
				order_date = None
				if len(ds) and ds != 'NULL':
					try:
						ds_split = ds.split(DATE_FIELD_SEPARATOR)
						order_date = datetime.date(int(ds_split[0]),int(ds_split[1]),int(ds_split[2]))
					except IndexError:
						loglist.append('Invalid Order Date %s -- file line %d' %(ds, counter))
						continue

			
				cMeterTrack = None
				try: # See if there is an existing record to update
					cMeterTrack = CustomerMeterTrack.objects.get(elster_meter_serial_number = elster_meter_serial_number, meter_barcode=meter_barcode, rma_number=rma_number)
					# Update ElsterMeterTrack
					cMeterTrack.meter_type = self.eval_for_null(row[self.columns['METER_TYPE']])
					cMeterTrack.meter_barcode = meter_barcode
					cMeterTrack.rma_number = rma_number
					cMeterTrack.order_date = order_date
					cMeterTrack.set_date = set_date
					cMeterTrack.reason_for_removal = self.eval_for_null(row[self.columns['REASON_FOR_REMOVAL']])
					cMeterTrack.customer_defined_failure_code = self.eval_for_null(row[self.columns['CUSTOMER_DEFINED_FAILURE_CODE']])
					cMeterTrack.failure_detail = self.eval_for_null(row[self.columns['FAILURE_DETAIL']])
					cMeterTrack.exposure = self.eval_for_null(row[self.columns['EXPOSURE']])
					cMeterTrack.shipment = shipment
					cMeterTrack.service_status = self.eval_for_null(row[self.columns['SERVICE_STATUS']])
					cMeterTrack.original_order_information = self.eval_for_null(row[self.columns['ORIGINAL_ORDER_INFORMATION']])
					cMeterTrack.longitude = self.eval_for_null(row[self.columns['LONGITUDE']])
					cMeterTrack.latitude = self.eval_for_null(row[self.columns['LATITUDE']])
					cMeterTrack.address = self.eval_for_null(row[self.columns['ADDRESS']])
				except ObjectDoesNotExist:                    
					# New CustomerMeterTrack
					cMeterTrack = CustomerMeterTrack(
						elster_meter_serial_number = elster_meter_serial_number,
						meter_barcode = meter_barcode,
						rma_number = rma_number,
						meter_type = self.eval_for_null(row[self.columns['METER_TYPE']]),
						order_date = order_date,
						set_date = set_date,
						failure_date = failure_date,
						reason_for_removal = self.eval_for_null(row[self.columns['REASON_FOR_REMOVAL']]),
						customer_defined_failure_code = self.eval_for_null(row[self.columns['CUSTOMER_DEFINED_FAILURE_CODE']]),
						failure_detail = self.eval_for_null(row[self.columns['FAILURE_DETAIL']]),
						exposure = self.eval_for_null(row[self.columns['EXPOSURE']]),
						shipment = shipment,
						service_status = self.eval_for_null(row[self.columns['SERVICE_STATUS']]),
						original_order_information = self.eval_for_null(row[self.columns['ORIGINAL_ORDER_INFORMATION']]),
						longitude = self.eval_for_null(row[self.columns['LONGITUDE']]),
						latitude = self.eval_for_null(row[self.columns['LATITUDE']]),
						
						address = self.eval_for_null(row[self.columns['ADDRESS']]),
						)
				try:
					with transaction.atomic():
						cMeterTrack.save()
				except DatabaseError, err:
					try:
						error_number, error_message = err
					except:
						error_message = err
						error_number = 0
					# Catch duplicate key error.
					if error_number != 1062:
						loglist.append(
							'Database Error: %s, Number: %d -- file line %d' % (error_message,
																error_number, counter))
				except OverflowError:
					pass
			except Exception as inst:
				exception_count += 1
				loglist.append('Import Error: %s at file line: %d' % (str(inst),counter))
				if (exception_count > MAX_EXCEPTIONS):
					loglist.append('Exceeded MAX_EXCEPTIONS: %d at file line: %d' % (exception_count,counter))
					break 

			if CSVIMPORT_LOG == 'logger':
				for line in loglist:
					logger.info(line)
			self.loglist.extend(loglist)
			loglist = []

		# clean up any items not caught from bailing
		if CSVIMPORT_LOG == 'logger':
			for line in loglist:
				logger.info(line)
		self.loglist.extend(loglist)
		loglist = []
		try:
			self.cloud_file.close()
		except err:
			loglist.append('Error %s, closing import file -- file line %d' % (str(err), counter))

		if self.loglist:
			self.props = {'file_name':self.file_name,
						  'import_user':'cron',
						  'upload_method':'cronjob',
						  'error_log':'\n'.join(loglist),
						  'import_date':datetime.datetime.now()}
			return self.loglist
		else:
			return ['No logging', ]

	def error(self, message, type=1):
		"""
		Types:
			0. A fatal error. The most drastic one. Will quit the program.
			1. A notice. Some minor thing is in disorder.
		"""

		types = (
			('Fatal error', FatalError),
			('Notice', None),
		)

		self.errors.append((message, type))

		if type == 0:
			# There is nothing to do. We have to quit at this point
			raise types[0][1], message
		elif self.debug == True:
			print "%s: %s" % (types[type][0], message)
