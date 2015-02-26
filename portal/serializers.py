from django.contrib.auth.models import User, Group
from portal.models import ElsterMeterCount, ElsterRmaDefect, ElsterMeterTrack, Shipment, ElsterRma
from csvimport.models import CSVImportCustomerMeterTrack, CSVImportElsterMeterTrack
from rest_framework import serializers


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = User
        fields = ('url', 'username', 'email', 'groups')


class GroupSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Group
        fields = ('url', 'name')

class ElsterMeterCountSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = ElsterMeterCount
		fields = ('url', 'meter_count', 'as_of_date')
		
class ElsterRmaDefectSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = ElsterRmaDefect

class ElsterRmaSerializer(serializers.HyperlinkedModelSerializer):
	class Meta:
		model = ElsterRma

class ShipmentSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Shipment
        fields = ('rma', 'originator', 'ship_date', 'tracking_number', 'carrier', 'notes')
        
class ElsterMeterTrackSerializer(serializers.ModelSerializer):
	meter_style = serializers.StringRelatedField()
	defect = serializers.StringRelatedField()

	class Meta:
		model = ElsterMeterTrack
		fields = ('url', 'elster_serial_number', 'meter_style',
			'meter_barcode', 'rma_number', 'rma_create_date',
			'rma_receive_date', 'rma_complete_date', 'defect', 
			'complaint', 'finding', 'action_taken')

class CSVImportCustomerMeterTrackSerializer(serializers.ModelSerializer):
	class Meta:
		model = CSVImportCustomerMeterTrack
		
class CSVImportElsterMeterTrackSerializer(serializers.ModelSerializer):
	class Meta:
		model = CSVImportElsterMeterTrack