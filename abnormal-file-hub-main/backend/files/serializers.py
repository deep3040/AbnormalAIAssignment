from rest_framework import serializers
from .models import File

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'file', 'original_filename', 'file_type', 'size', 'file_hash', 'uploaded_at']
        read_only_fields = ['id', 'file_hash', 'uploaded_at'] 