from django.contrib.auth.models import User
from django.db import models, transaction
from django.db.models import Q
from allauth.account.models import EmailAddress
from allauth.socialaccount.models import SocialAccount
import hashlib
from django.utils import timezone
from django.core.exceptions import ValidationError
import datetime
from django.core.exceptions import ObjectDoesNotExist

def utc_to_local(utc_dt):
    return utc_dt.replace(tzinfo=timezone.utc).astimezone(timezone.get_current_timezone())
    
class ElsterMeterType(models.Model):
    def __unicode__(self):
        if self.description:
            return ("%s:%s"%(self.description, self.style))
        else:
            return("%s"%(self.style))
        
    OTHER_M = 'OT'
    REX = 'ZF'
    GRX = 'ZQ'
    GAS = 'EG'
    WAT = 'EW'
    MGK = 'ZD'
    NMG = '7S31'
    RPT = '7S40'
    METER_TYPE_CHOICES= (
        (REX, 'REX'),
        (GRX, 'GREX'),
        (GAS, 'Gas module'),
        (WAT, 'Water module'),
        (MGK, 'Gatekeeper (metered)'),
        (NMG, 'Gatekeeper (non-metered)'),
        (RPT, 'Repeater'),
        (OTHER_M, 'Other'),
    )
    
    C_ELE = 'E'
    C_WAT = 'W'
    C_GAS = 'G'
    METER_CATEGORY_CHOICES=(
        (C_ELE, 'Electric'),
        (C_WAT, 'Water'),
        (C_GAS, 'Gas'),
    )
    
    style =  models.CharField(max_length = 15, verbose_name="Manufacturer Style")
    category =  models.CharField(max_length = 1, choices = METER_CATEGORY_CHOICES, default=C_ELE, verbose_name="Meter Category")
    description = models.CharField(max_length = 50, null=True, blank=True)
    
    @property
    def meter_style_to_type(self):
        if self.meter_style:
            type=[ms[1] for ms in ElsterMeterType.METER_TYPE_CHOICES if ms[0].lower() in (self.style).lower()]
            if len(type):
                return type
            else:
                return 'No Style Match %s'%self.style
        else:
            return ''

class ElsterRmaDefect(models.Model):
    def __unicode__(self):
        if self.description:
            return (self.description)
        else:
            return ("%03d"%self.defect_id)
        
    defect_id = models.PositiveSmallIntegerField(verbose_name="Defect ID after root cause analysis")
    description = models.CharField(max_length=300, verbose_name="Defect Code (description)",null=True, blank=True)
    failure = models.BooleanField(default=True, verbose_name="Defect is a counted a Failure")

class ElsterMeterCount(models.Model):
    def __unicode__(self):
        return ("%d as of %s"%(self.meter_count, self.as_of_date))

    meter_count = models.PositiveIntegerField(verbose_name="Meter Count")
    as_of_date = models.DateField(default=datetime.date.today)
    
class ElsterRma(models.Model):
    def __unicode__(self):
        return self.number
    class Meta:
        ordering = ["complete_date"]
        verbose_name = 'RMA'
        verbose_name_plural = 'RMA\'s'
    number = models.CharField(max_length=100, unique=True, verbose_name="Elster RMA Number")
    create_date = models.DateField(null=True, blank=True)
    receive_date = models.DateField(null=True, blank=True)
    complete_date = models.DateField(null=True, blank=True)
    
    @property
    def elster_meter_count(self):
        return ElsterMeterTrack.objects.filter(rma=self).count()

class Shipment(models.Model):
    def __unicode__(self):
        return ("%s/%s"%(self.rma_number, self.originator))
    # shipment type choices
    CUSTOMER = 'CUSTOMER'
    ELSTER = 'ELSTER'
    OTHER = 'OTHER'
    SHIPMENT_ORIGINATOR_CHOICES = (
        (CUSTOMER, 'Customer'),
        (ELSTER, 'Elster'),
        (OTHER, 'Other'),
    )
    
    rma = models.ForeignKey(ElsterRma, null=False, verbose_name="RMA Reference for Shipment")
    originator = models.CharField(max_length=10, choices = SHIPMENT_ORIGINATOR_CHOICES, default=CUSTOMER, verbose_name = "Originator") 
    ship_date = models.DateField(null=True, blank=True,verbose_name="Shipment Date")
    tracking_number = models.CharField(max_length=25, null=True,blank=True,verbose_name="Shipment Tracking Number")
    carrier = models.CharField(max_length=25, null=True,blank=True)
    notes = models.TextField(max_length=2000, null=True, blank=True)

    @property
    def rma_number(self):
        if self.rma:
            return self.rma.number
        else:
            return ''         

class ElsterMeterTrack(models.Model):

    def __unicode__(self):
        return ("%s/%s"%(self.elster_serial_number, self.meter_barcode))

    elster_serial_number = models.CharField(max_length=100, )
    meter_style = models.ForeignKey(ElsterMeterType, null=True, blank=True,verbose_name="Elster Meter Type")
    meter_barcode = models.CharField(max_length=100,null=True, blank=True)
    manufacture_date = models.DateField(null=True, blank=True)
    #purchase_date = models.DateField(null=True, blank=True)
    #ship_date = models.DateField(null=True, blank=True)
    rma = models.ForeignKey(ElsterRma, null=True, blank=True, verbose_name="Assigned RMA")
    defect = models.ForeignKey(ElsterRmaDefect, null=True, blank=True, verbose_name="Defect after root cause analysis")
    complaint = models.CharField(max_length=300, verbose_name="Customer Complaint",null=True, blank=True)
    finding = models.CharField(max_length=300,null=True,blank=True)
    action_taken = models.CharField(max_length=300, verbose_name="Elster action",null=True, blank=True)
    
    class Meta:
        unique_together = (("elster_serial_number","meter_barcode","rma"),)
        ordering = ["elster_serial_number"]
        verbose_name = 'Elster RMA\'d Meters'
        verbose_name_plural = 'Elster Meter RMAs'
        
    @property
    def meter_style_description(self):
        if self.meter_style:
            if self.meter_style.description:
                return self.meter_style.description
            else:
                return self.meter_style.style
        else:
            return ''

    @property
    def rma_number(self):
        if self.rma:
            return self.rma.number
        else:
            return ''
                        
    @property
    def rma_create_date(self):
        value = ''
        if self.rma:
            if self.rma.create_date:
                value = self.rma.create_date
        return value

    @property
    def rma_receive_date(self):
        value = ''
        if self.rma:
            if self.rma.receive_date:
                value = self.rma.receive_date
        return value

    @property
    def rma_complete_date(self):
        value = ''
        if self.rma:
            if self.rma.complete_date:
                value = self.rma.complete_date
        return value
        
    @property
    def defect_id_desc(self):
        if self.defect:
            return self.defect.description
        else:
            return ''
            
    def clean(self):
        if self.elster_serial_number is None:
            raise ValidationError('Elster Serial Number must be filled in')
        elif len(self.elster_serial_number) == 0:
            raise ValidationError('Elseter Serial Number must be filled in')
            
        # validate dates
        if self.rma:
            if self.rma.create_date is not None and self.manufacture_date is not None:
                if self.rma.create_date < self.manufacture_date:
                    raise ValidationError('RMA Create Date may not preceed Manufacture Date')
                        
            if self.rma.receive_date is not None and self.rma.complete_date is not None:
                if self.rma.complete_date < self.rma.receive_date:
                    raise ValidationError('RMA Complete Date may not preceed RMA Receive Date')
                
            # validate defect entry
            if self.rma.complete_date is not None and self.defect is None:
                raise ValidationError('Defect Code may not be empty when RMA Complete Date is entered')

class CustomerMeterTrack(models.Model):
    def __unicode__(self):
        return ("Serial#:%s Barcode:%s Failure_Date:%s"%(self.elster_meter_serial_number, str(self.meter_barcode), str(self.failure_date),))

    # Orientation choices
    NORTH = 'N'
    SOUTH = 'S'
    EAST = 'E'
    WEST = 'W'
    METER_EXPOSURE_CHOICES = (
        (NORTH, 'North'),
        (SOUTH, 'South'),
        (EAST, 'East'),
        (WEST, 'West'),
    )
    
    # service choices
    IN_FIELD = 'F'
    IN_INVENTORY = 'I'
    METER_SERVICE_CHOICES = (
        (IN_FIELD, 'In Field'),
        (IN_INVENTORY, 'Inventoried'),
    )
    
    # Reason for removal
    VISUAL_DAMAGE = 'VISUAL_DAMAGE'     # Visual damage noted
    INTERMIITTENT = 'INTERMITTENT_PERF' # Intermittent performance
    DISPLAY = 'DISPLAY NOOP'            # Display not functioning
    RADIO = 'NOT_COMMUNICATING'         # Not readable remotely
    NFUNC = 'NOT_FUNCTIONING'           # Not functioning
    DISCONNECT = 'DISCO_SW_BROKEN'      # Disconnect switch not functioning
    OTHER_D = 'OTHER'                   # Other
    
    REMOVAL_REASON_CHOICES = (
        (VISUAL_DAMAGE, 'Visual damage noted'),
        (INTERMIITTENT, 'Intermittent performance'),
        (DISPLAY,'Display not functioning'),
        (RADIO,'Not readable remotely'),
        (NFUNC,'Not functioning'),
        (DISCONNECT,'Disconnect switch not functioning'),
        (OTHER_D,'Other'),
    )
    
    # meter type choices
    OTHER_M = 'OT'
    REX = 'ZF'
    GRX = 'ZQ'
    GAS = 'EG'
    WAT = 'EW'
    MGK = 'ZD'
    NMG = '7S31'
    RPT = '7S40'
    METER_TYPE_CHOICES = (
        (REX, 'REX'),
        (GRX, 'GREX'),
        (GAS, 'Gas module'),
        (WAT, 'Water module'),
        (MGK, 'A3 or Gatekeeper (metered)'),
        (NMG, 'Gatekeeper (non-metered)'),
        (RPT, 'Repeater'),
        (OTHER_M, 'Other'),
    )
    
    elster_meter_serial_number = models.CharField(max_length=100,  verbose_name="Meter Number")
    meter_type = models.CharField(max_length = 15, null=True, blank=True, choices = METER_TYPE_CHOICES, default=REX,  verbose_name="Meter Type")
    meter_barcode = models.CharField(max_length=100)
    rma = models.ForeignKey(ElsterRma, verbose_name="Assigned RMA")
    order_date = models.DateField(null=True, blank=True,verbose_name="Meter Order, Purchase or Reciept Date")
    set_date = models.DateField(null=True, blank=True,verbose_name="Meter Set Date")
    failure_date = models.DateField(null=True, blank=True,verbose_name="Meter Remove Date")
    #reason_for_removal = models.CharField(max_length=500,null=True,blank=True, choices = REMOVAL_REASON_CHOICES, default=OTHER_D, verbose_name="Complaint")
    reason_for_removal = models.CharField(max_length=500,null=True,blank=True,  verbose_name="Complaint")
    customer_defined_failure_code = models.CharField(max_length=50,null=True,blank=True, verbose_name="Customer reference Defect Code")
    comments = models.TextField(max_length=2000, null=True, blank=True)
    failure_detail = models.TextField(max_length=2000, verbose_name="Detailed Description",null=True, blank=True)
    exposure = models.CharField(max_length = 1, null=True,blank=True, choices = METER_EXPOSURE_CHOICES, verbose_name="Meter Facing Direction")
    pallet = models.CharField(max_length=25, null=True, blank=True, verbose_name="Pallet Information")
    original_order_information = models.CharField(max_length=100,null=True, blank=True,)
    service_status = models.CharField(max_length=1,null=True,blank=True, choices = METER_SERVICE_CHOICES, default=IN_INVENTORY)
    longitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,verbose_name="Meter Longitude Position")
    latitude = models.DecimalField(max_digits=12, decimal_places=6, null=True, blank=True,verbose_name="Meter Latitude Position")
    address = models.TextField(max_length=2000, verbose_name="Removed location address",null=True, blank=True)
    
    class Meta:
        unique_together = (("elster_meter_serial_number","meter_barcode","rma"),)
        ordering = ["meter_barcode"]
        verbose_name = 'Customer RMA\'d Meter'
        verbose_name_plural = 'Customer Meter RMAs'

    @property
    def rma_number(self):
        if self.rma:
            return self.rma.number
        else:
            return ''
                        
    @property
    def rma_create_date(self):
        value = ''
        if self.rma:
            if self.rma.create_date:
                value = self.rma.create_date
        return value

    @property
    def rma_receive_date(self):
        value = ''
        if self.rma:
            if self.rma.receive_date:
                value = self.rma.receive_date
        return value

    @property
    def rma_complete_date(self):
        value = ''
        if self.rma:
            if self.rma.complete_date:
                value = self.rma.complete_date
        return value
     
        
class UserProfile(models.Model):
    user = models.OneToOneField(User, related_name='profile')

    def __unicode__(self):
        #return "{}'s profile".format(self.user.username)
        return format(self.user.username)

    class Meta:
        db_table = 'user_profile'

    def account_verified(self):
        if self.user.is_authenticated:
            result = EmailAddress.objects.filter(email=self.user.email)
            if len(result):
                return result[0].verified
        return False

    def profile_image_url(self):
        fb_uid = SocialAccount.objects.filter(user_id=self.user.id, provider='facebook')
    
        if len(fb_uid):
            return "http://graph.facebook.com/{}/picture?width=40&height=40".format(fb_uid[0].uid)
    
        return "http://www.gravatar.com/avatar/{}?s=40".format(hashlib.md5(self.user.email).hexdigest())
    
    @staticmethod
    def default_user_profile():
        try:
            default_user_profile = UserProfile.objects.get(user__username='default')
        except ObjectDoesNotExist:
            default_user = User.objects.create(username='default', first_name='default', last_name='default')
            default_user.save()
            default_user_profile = UserProfile.objects.create(user=default_user)
            default_user_profile.save()
        return default_user_profile
    
User.profile = property(lambda u: UserProfile.objects.get_or_create(user=u)[0])

class Account(models.Model):
    def __unicode__(self):
        return ("%s:%s"%(self.name, self.verification))
    name = models.CharField(max_length=25,  verbose_name="Account name")
    verification = models.CharField(max_length = 25,  verbose_name="Verification code")

