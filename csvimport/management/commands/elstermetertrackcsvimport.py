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
	Parse and import a CSV file to portal.ElsterMeterTrack

	During import existing users will attempt to be matched by "elster_serial_number","meter_barcode","rma_number, 
	Any ElsterMeterTrack entry that already exist will be updated. 
	"""

	option_list = BaseCommand.option_list + (
			   make_option('--file_name', default='elster_meter_track.csv',	help='Please provide the file to import from'),
			   make_option('--charset', default='', help='Force the charset conversion used rather than detect it'))
	help = "Imports a CSV file to the ElsterMeterTrack model"


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
			'ELSTER_SERIAL_NUMBER':0,
			'METER_STYLE':1,
			'METER_BARCODE':2,
			'MANUFACTURE_DATE':3,
			'RMA_NUMBER':4,
			'RMA_CREATE_DATE':5,
			'RMA_RECEIVE_DATE':6,
			'RMA_COMPLETE_DATE':7,
			'DEFECT_ID':8,
			'DEFECT_ID_DESC':9,
			'COMPLAINT':10,
			'FINDING':11,
			'ACTION_TAKEN':12,
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

				elster_serial_number = self.eval_for_null(row[self.columns['ELSTER_SERIAL_NUMBER']])
				if elster_serial_number == None:
					exception_count += 1
					loglist.append('Import Error:Elster Serial Number NULL - skipping record -- file line %d' % counter)
					if (exception_count > MAX_EXCEPTIONS):
						loglist.append('Exceeded MAX_EXCEPTIONS: %d at file line: %d' % (exception_count,counter))
						break 
					else:
						continue
				meter_barcode = self.eval_for_null(row[self.columns['METER_BARCODE']])
				rma_number = self.eval_for_null(row[self.columns['RMA_NUMBER']])
				
				# Pull the date fields
				ds = row[self.columns['MANUFACTURE_DATE']]
				manufacture_date = None
				if len(ds)  and ds != 'NULL':
					try:
						ds_split = ds.split(DATE_FIELD_SEPARATOR)
						manufacture_date = datetime.date(int(ds_split[0]),int(ds_split[1]),int(ds_split[2]))
					except IndexError:
						loglist.append('Invalid Manufacture Date %s -- file line %d' %(ds, counter))
						continue
				
				ds = row[self.columns['RMA_CREATE_DATE']]
				rma_create_date = None
				if len(ds) and ds != 'NULL':
					try:
						ds_split = ds.split(DATE_FIELD_SEPARATOR)
						rma_create_date = datetime.date(int(ds_split[0]),int(ds_split[1]),int(ds_split[2]))
					except IndexError:
						loglist.append('Invalid RMA Create Date %s -- file line %d' %(ds, counter))
						continue

				ds = row[self.columns['RMA_RECEIVE_DATE']]
				rma_receive_date = None
				if len(ds) and ds != 'NULL':
					try:
						ds_split = ds.split(DATE_FIELD_SEPARATOR)
						rma_receive_date = datetime.date(int(ds_split[0]),int(ds_split[1]),int(ds_split[2]))
					except IndexError:
						loglist.append('Invalid RMA Receive Date %s -- file line %d' %(ds, counter))
						continue

				ds = row[self.columns['RMA_COMPLETE_DATE']]
				rma_complete_date = None
				if len(ds) and ds != 'NULL':
					try:
						ds_split = ds.split(DATE_FIELD_SEPARATOR)
						rma_complete_date = datetime.date(int(ds_split[0]),int(ds_split[1]),int(ds_split[2]))
					except IndexError:
						loglist.append('Invalid RMA Complete Date %s -- file line %d' %(ds, counter))
						continue
						
				defect_id_str = self.eval_for_null(row[self.columns['DEFECT_ID']])
				defect_id = None
				if defect_id_str != None:
					defect_id = int(defect_id_str)
					
				meter_style = self.eval_for_null(row[self.columns['METER_STYLE']])
				if meter_style == None:
					meter_style = 'Other'
					
				eMeterTrack = None
				try: # See if there is an existing record to update
					eMeterTrack = ElsterMeterTrack.objects.get(elster_serial_number = elster_serial_number, meter_barcode=meter_barcode, rma_number=rma_number)
					# Update ElsterMeterTrack
					eMeterTrack.meter_style = meter_style
					eMeterTrack.meter_barcode = meter_barcode
					eMeterTrack.manufacture_date = manufacture_date
					eMeterTrack.rma_number = self.eval_for_null(row[self.columns['RMA_NUMBER']])
					eMeterTrack.rma_create_date = rma_create_date
					eMeterTrack.rma_receive_date = rma_receive_date
					eMeterTrack.rma_complete_date = rma_complete_date
					eMeterTrack.defect_id = defect_id
					eMeterTrack.defect_id_desc = self.eval_for_null(row[self.columns['DEFECT_ID_DESC']])
					eMeterTrack.complaint = self.eval_for_null(row[self.columns['COMPLAINT']])
					eMeterTrack.finding = self.eval_for_null(row[self.columns['FINDING']])
					eMeterTrack.action_taken = self.eval_for_null(row[self.columns['ACTION_TAKEN']])
				except ObjectDoesNotExist:                    
					# New ElsterMeterTrack
					eMeterTrack = ElsterMeterTrack(
						elster_serial_number = elster_serial_number,
						meter_style = meter_style
						meter_barcode = meter_barcode,
						manufacture_date = manufacture_date,
						rma_number = self.eval_for_null(row[self.columns['RMA_NUMBER']]),
						rma_create_date = rma_create_date,
						rma_receive_date = rma_receive_date,
						rma_complete_date = rma_complete_date,
						defect_id = defect_id,
						defect_id_desc = self.eval_for_null(row[self.columns['DEFECT_ID_DESC']]),
						complaint =  self.eval_for_null(row[self.columns['COMPLAINT']]),
						finding = self.eval_for_null(row[self.columns['FINDING']]),
						action_taken =  self.eval_for_null(row[self.columns['ACTION_TAKEN']])
						)
				try:
					with transaction.atomic():
						eMeterTrack.save()
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
