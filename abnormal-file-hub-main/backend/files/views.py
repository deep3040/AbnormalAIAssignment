
from django.shortcuts import render
from django.db import models
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
import hashlib
from .models import File
from .serializers import FileSerializer

# Create your views here.

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer

    def get_queryset(self):
        queryset = File.objects.all()
        
        # Search by filename
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(original_filename__icontains=search)
            
        # Filter by file type
        file_type = self.request.query_params.get('file_type')
        if file_type:
            queryset = queryset.filter(file_type__icontains=file_type)
            
        # Filter by size
        min_size = self.request.query_params.get('min_size')
        max_size = self.request.query_params.get('max_size')
        if min_size:
            queryset = queryset.filter(size__gte=min_size)
        if max_size:
            queryset = queryset.filter(size__lte=max_size)
            
        # Filter by date
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        if start_date:
            queryset = queryset.filter(uploaded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(uploaded_at__lte=end_date)
            
        return queryset

    def create(self, request, *args, **kwargs):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({'error': 'No file provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate file hash
        hasher = hashlib.sha256()
        for chunk in file_obj.chunks():
            hasher.update(chunk)
        file_hash = hasher.hexdigest()
        
        # Check for duplicates
        existing_file = File.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            # Create new record pointing to existing file
            new_file = File(
                original_filename=file_obj.name,
                file_type=file_obj.content_type,
                size=file_obj.size,
                file_hash=file_hash,
                file=existing_file.file 
            )
            new_file.save()
            serializer = self.get_serializer(new_file)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        # Prepare data for new file
        data = {
            'file': file_obj,
            'original_filename': file_obj.name,
            'file_type': file_obj.content_type,
            'size': file_obj.size
        }
        
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        # Save with hash
        serializer.save(file_hash=file_hash)
        
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get storage stats including savings from deduplication"""
        total_size = File.objects.aggregate(total=models.Sum('size'))['total'] or 0
        
        # Calculate size of unique files based on hash
        # We group by hash and take the max size (should be same for all with same hash)
        unique_size = File.objects.values('file_hash').annotate(
            file_size=models.Max('size')
        ).aggregate(total=models.Sum('file_size'))['total'] or 0
        
        saved_size = total_size - unique_size
        
        return Response({
            'total_size': total_size,
            'unique_size': unique_size,
            'saved_size': saved_size,
            'savings_percentage': (saved_size / total_size * 100) if total_size > 0 else 0
        })

    @action(detail=False, methods=['get', 'post'], url_path='dedup-check')
    def dedup_check(self, request):
        """Check if file hash exists and create duplicate link if so"""
        file_hash = request.data.get('file_hash')
        filename = request.data.get('filename')
        file_type = request.data.get('file_type')
        size = request.data.get('size')
        
        if not all([file_hash, filename, size]):
             return Response({'error': 'Missing required fields'}, status=status.HTTP_400_BAD_REQUEST)
             
        existing_file = File.objects.filter(file_hash=file_hash).first()
        
        if existing_file:
            # Create new record pointing to existing file immediately
            new_file = File(
                original_filename=filename,
                file_type=file_type,
                size=size,
                file_hash=file_hash,
                file=existing_file.file
            )
            new_file.save()
            serializer = self.get_serializer(new_file)
            return Response({'exists': True, 'file': serializer.data}, status=status.HTTP_200_OK)
            
        return Response({'exists': False}, status=status.HTTP_200_OK)
