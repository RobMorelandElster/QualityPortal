from django.test import TestCase
from django.test.client import Client

from csvimport.models import *
from mdm.models import *
from django.utils import timezone
from django.core.urlresolvers import reverse
from django.db import IntegrityError
from django.core.exceptions import ObjectDoesNotExist

class TestImport(TestCase):
	def test_constraint(self):
		try:
			# Duplicates should be prevented.
			acct=Account.objects.create(number='acct1')
			org1=Org.objects.create(name='org1')
			org2=Org.objects.create(name='org2')
			AccountOwnership.objects.create(org=org1,account=acct)
			self.assertTrue(1,'One unique account allowed')
			AccountOwnership.objects.create(org=org2,account=acct)
			self.assertTrue(0, 'Duplicate account allowed.')
		except IntegrityError:
			pass
			
	def test_new_account_ownership(self):
		new_acct=Account.objects.create(number='new_acct')
		org1=Org.objects.create(name='org1')
		try:
			exist_org = Account.objects.get(org=org1)
			self.assertTrue(0, 'Account shouldnt be in org1')
		except ObjectDoesNotExist:
			pass
			
		try:
			acct_ownership = AccountOwnership.objects.get(account=new_acct)
			self.assertTrue(0, "Account shouldn't be in AccountOnwership table")
		except ObjectDoesNotExist:
			pass
			
		try:
			AccountOwnership.objects.create(org=org1,account=new_acct)
			self.assertTrue(1,'Account added to org1')
			acct_ownership = AccountOwnership.objects.get(account=new_acct,org=org1)
			self.assertTrue(1,"Account properly assigned to org1")
		except IntegrityError:
			self.assertTrue(0,"Account couldn't be added to single org")
			
		try: # if acct_ownership assign to new org
			org2=Org.objects.create(name='org2')
			acct_ownership = AccountOwnership.objects.get(account=new_acct)
			acct_ownership.org=org2
			acct_ownership.save()
		except ObjectDoesNotExist:
			self.assertTrue(0,"Account should have been in Account Ownership")
		except IntegrityError:
			self.assertTrue(0,"Account couldn't be switched to new org2")			
		