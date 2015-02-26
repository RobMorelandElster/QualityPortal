from django.contrib.auth.models import User, Group
from django.core.files.storage import default_storage
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework import viewsets, views, authentication, permissions
from rest_framework.response import Response
from rest_framework import status
from portal.serializers import *
from rest_framework.parsers import MultiPartParser, FileUploadParser, FormParser
from csvimport.models import *
from portal.tasks import processElsterMeterTrackImportFile, processCustomerMeterTrackImportFile

import traceback
        
'''
Example call:
    curl -i -u username:pword -F file_name=test.csv -F upload_file=@local_file.csv 
        https://elster-qp.herokuapp.com/customer_csv_import_file/
'''
@api_view(['POST','GET',])
def customer_csv_import_file(request, format=None):
    parser_classes = (MultiPartParser, FormParser,FileUploadParser,)
    if request.method == 'POST':
        try:
            upload_file = request.FILES['upload_file']
            file_name = get_file_path(None, request.DATA['file_name'])
            
            print("Processing customer_csv_import_file upload_file:%s, file_name:%s"%(upload_file, file_name))
            with default_storage.open(file_name, 'wb+') as temp_file:
                print("About to upload file chunks")
                for chunk in upload_file.chunks():
                    print("Uploading chunk")
                    temp_file.write(chunk)
            print("Finished uploading file: %s"%file_name)    
            cmti = CSVImportCustomerMeterTrack.objects.create(upload_file=file_name, 
                file_name=file_name,
                import_user=request.user,
                import_date=timezone.now(),
                upload_method='rest-api',)

            result = processCustomerMeterTrackImportFile.delay('utf-8', cmti, request.user.username)
            task_id = result.id
            if result.traceback:
                cmti.error_log = cmti.error_log + ('\nTask ID:%s Error:%s'%(task_id, result.traceback))
            cmti.save()
            
            serializer = CSVImportCustomerMeterTrackSerializer(cmti, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as err:
            tb = traceback.format_exc()
            print (tb) 
            return Response(tb , status=status.HTTP_400_BAD_REQUEST)   
    elif request.method == 'GET':
        try:
            csv_customer_import_files = CSVImportCustomerMeterTrack.objects.all()
            serializer = CSVImportCustomerMeterTrackSerializer(csv_customer_import_files, many=True)
            return Response(serializer.data)
        except Exception as err:
            tb = traceback.format_exc()
            print (tb) 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST','GET',])
def elster_csv_import_file(request, format=None):
    parser_classes = (MultiPartParser, FormParser,FileUploadParser,)
    if request.method == 'POST':
        try:
            upload_file = request.FILES['upload_file']
            file_name = get_file_path(None, request.DATA['file_name'])
            
            print("Processing elster_csv_import_file upload_file:%s, file_name:%s"%(upload_file, file_name))
            with default_storage.open(file_name, 'wb+') as temp_file:
                print("About to upload file chunks")
                for chunk in upload_file.chunks():
                    print("Uploading chunk")
                    temp_file.write(chunk)
            print("Finished uploading file: %s"%file_name)    
            cmti = CSVImportElsterMeterTrack.objects.create(upload_file=file_name, 
                file_name=file_name,
                import_user=request.user,
                import_date=timezone.now(),
                upload_method='rest-api',)

            result = processElsterMeterTrackImportFile.delay('utf-8', cmti, request.user.username)
            task_id = result.id
            if result.traceback:
                cmti.error_log = cmti.error_log + ('\nTask ID:%s Error:%s'%(task_id, result.traceback))
            cmti.save()
            
            serializer = CSVImportElsterMeterTrackSerializer(cmti, many=False)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        except Exception as err:
            tb = traceback.format_exc()
            print (tb) 
            return Response(tb , status=status.HTTP_400_BAD_REQUEST)   
    elif request.method == 'GET':
        try:
            csv_elster_import_files = CSVImportElsterMeterTrack.objects.all()
            serializer = CSVImportElsterMeterTrackSerializer(csv_elster_import_files, many=True)
            return Response(serializer.data)
        except Exception as err:
            tb = traceback.format_exc()
            print (tb) 
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows users to be viewed or edited.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer


class GroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Group.objects.all()
    serializer_class = GroupSerializer
    
class ElsterMeterCountViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = ElsterMeterCount.objects.all()
    serializer_class = ElsterMeterCountSerializer

class ElsterRmaDefectViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = ElsterRmaDefect.objects.all()
    serializer_class = ElsterRmaDefectSerializer

class ElsterRmaViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = ElsterRma.objects.all()
    serializer_class = ElsterRmaSerializer

class ElsterMeterTrackViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = ElsterMeterTrack.objects.all()
    serializer_class = ElsterMeterTrackSerializer

class ShipmentViewSet(viewsets.ModelViewSet):
    """
    API endpoint that allows groups to be viewed or edited.
    """
    queryset = Shipment.objects.all()
    serializer_class = ShipmentSerializer