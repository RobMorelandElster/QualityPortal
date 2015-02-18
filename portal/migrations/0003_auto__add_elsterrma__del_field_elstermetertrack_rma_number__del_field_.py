# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Removing unique constraint on 'ElsterMeterTrack', fields ['elster_serial_number', 'meter_barcode', 'rma_number']
        db.delete_unique(u'portal_elstermetertrack', ['elster_serial_number', 'meter_barcode', 'rma_number'])

        # Adding model 'ElsterRma'
        db.create_table(u'portal_elsterrma', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('number', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('create_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('receive_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('complete_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal(u'portal', ['ElsterRma'])

        # Deleting field 'ElsterMeterTrack.rma_number'
        db.delete_column(u'portal_elstermetertrack', 'rma_number')

        # Deleting field 'ElsterMeterTrack.rma_create_date'
        db.delete_column(u'portal_elstermetertrack', 'rma_create_date')

        # Deleting field 'ElsterMeterTrack.rma_complete_date'
        db.delete_column(u'portal_elstermetertrack', 'rma_complete_date')

        # Deleting field 'ElsterMeterTrack.rma_receive_date'
        db.delete_column(u'portal_elstermetertrack', 'rma_receive_date')

        # Adding field 'ElsterMeterTrack.rma'
        db.add_column(u'portal_elstermetertrack', 'rma',
                      self.gf('django.db.models.fields.related.ForeignKey')(to=orm['portal.ElsterRma'], null=True, blank=True),
                      keep_default=False)

        # Adding unique constraint on 'ElsterMeterTrack', fields ['elster_serial_number', 'meter_barcode', 'rma']
        db.create_unique(u'portal_elstermetertrack', ['elster_serial_number', 'meter_barcode', 'rma_id'])


    def backwards(self, orm):
        # Removing unique constraint on 'ElsterMeterTrack', fields ['elster_serial_number', 'meter_barcode', 'rma']
        db.delete_unique(u'portal_elstermetertrack', ['elster_serial_number', 'meter_barcode', 'rma_id'])

        # Deleting model 'ElsterRma'
        db.delete_table(u'portal_elsterrma')

        # Adding field 'ElsterMeterTrack.rma_number'
        db.add_column(u'portal_elstermetertrack', 'rma_number',
                      self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True),
                      keep_default=False)

        # Adding field 'ElsterMeterTrack.rma_create_date'
        db.add_column(u'portal_elstermetertrack', 'rma_create_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'ElsterMeterTrack.rma_complete_date'
        db.add_column(u'portal_elstermetertrack', 'rma_complete_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Adding field 'ElsterMeterTrack.rma_receive_date'
        db.add_column(u'portal_elstermetertrack', 'rma_receive_date',
                      self.gf('django.db.models.fields.DateField')(null=True, blank=True),
                      keep_default=False)

        # Deleting field 'ElsterMeterTrack.rma'
        db.delete_column(u'portal_elstermetertrack', 'rma_id')

        # Adding unique constraint on 'ElsterMeterTrack', fields ['elster_serial_number', 'meter_barcode', 'rma_number']
        db.create_unique(u'portal_elstermetertrack', ['elster_serial_number', 'meter_barcode', 'rma_number'])


    models = {
        u'auth.group': {
            'Meta': {'object_name': 'Group'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': u"orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        u'auth.permission': {
            'Meta': {'ordering': "(u'content_type__app_label', u'content_type__model', u'codename')", 'unique_together': "((u'content_type', u'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['contenttypes.ContentType']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        u'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Group']"}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "u'user_set'", 'blank': 'True', 'to': u"orm['auth.Permission']"}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        u'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        u'portal.account': {
            'Meta': {'object_name': 'Account'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '25'}),
            'verification': ('django.db.models.fields.CharField', [], {'max_length': '25'})
        },
        u'portal.customermetertrack': {
            'Meta': {'ordering': "['meter_barcode']", 'unique_together': "(('elster_meter_serial_number', 'meter_barcode', 'rma_number'),)", 'object_name': 'CustomerMeterTrack'},
            'address': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'comments': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            'customer_defined_failure_code': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'elster_meter_serial_number': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'exposure': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'failure_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'failure_detail': ('django.db.models.fields.TextField', [], {'max_length': '2000', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'latitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '6', 'blank': 'True'}),
            'longitude': ('django.db.models.fields.DecimalField', [], {'null': 'True', 'max_digits': '12', 'decimal_places': '6', 'blank': 'True'}),
            'meter_barcode': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'meter_type': ('django.db.models.fields.CharField', [], {'default': "'ZF'", 'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'order_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'original_order_information': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'reason_for_removal': ('django.db.models.fields.CharField', [], {'max_length': '500', 'null': 'True', 'blank': 'True'}),
            'rma_number': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'service_status': ('django.db.models.fields.CharField', [], {'default': "'I'", 'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'set_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'shipment': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.Shipment']", 'null': 'True', 'blank': 'True'})
        },
        u'portal.elstermetercount': {
            'Meta': {'object_name': 'ElsterMeterCount'},
            'as_of_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'meter_count': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        u'portal.elstermetertrack': {
            'Meta': {'ordering': "['elster_serial_number']", 'unique_together': "(('elster_serial_number', 'meter_barcode', 'rma'),)", 'object_name': 'ElsterMeterTrack'},
            'action_taken': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'complaint': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'defect': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.ElsterRmaDefect']", 'null': 'True', 'blank': 'True'}),
            'elster_serial_number': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'finding': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'manufacture_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'meter_barcode': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'meter_style': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.ElsterMeterType']", 'null': 'True', 'blank': 'True'}),
            'rma': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['portal.ElsterRma']", 'null': 'True', 'blank': 'True'})
        },
        u'portal.elstermetertype': {
            'Meta': {'object_name': 'ElsterMeterType'},
            'category': ('django.db.models.fields.CharField', [], {'default': "'E'", 'max_length': '1'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'style': ('django.db.models.fields.CharField', [], {'max_length': '15'})
        },
        u'portal.elsterrma': {
            'Meta': {'object_name': 'ElsterRma'},
            'complete_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'create_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'number': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'receive_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'})
        },
        u'portal.elsterrmadefect': {
            'Meta': {'object_name': 'ElsterRmaDefect'},
            'defect_id': ('django.db.models.fields.PositiveSmallIntegerField', [], {}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '300', 'null': 'True', 'blank': 'True'}),
            'failure': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        u'portal.shipment': {
            'Meta': {'object_name': 'Shipment'},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pallet_number': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'reference_id': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '25'}),
            'ship_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'tracking_number': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'})
        },
        u'portal.userprofile': {
            'Meta': {'object_name': 'UserProfile', 'db_table': "'user_profile'"},
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'profile'", 'unique': 'True', 'to': u"orm['auth.User']"})
        }
    }

    complete_apps = ['portal']