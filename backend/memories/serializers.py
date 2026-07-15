#!/usr/bin/env python3
from rest_framework import serializers
from .models import Memory

class MemorySerializer(serializers.ModelSerializer):
    uploader_name = serializers.CharField(source='uploaded_by.user.get_full_name', read_only=True)
    file_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    tagged_participants = serializers.SerializerMethodField()
    
    class Meta:
        model = Memory
        fields = [
            'id', 'media_type', 'file_url', 'thumbnail_url', 'caption', 
            'uploader_name', 'created_at', 'tagged_participants', 'is_active'
        ]
        read_only_fields = ['id', 'created_at']

    def get_file_url(self, obj):
        if not obj.file:
            return None
        if hasattr(obj.file, 'url'):
            return obj.file.url
        if isinstance(obj.file, str):
            from cloudinary.utils import cloudinary_url
            url, _ = cloudinary_url(obj.file, resource_type=obj.media_type)
            return url
        return str(obj.file)
        
    def get_thumbnail_url(self, obj):
        return obj.thumbnail_url
        
    def get_tagged_participants(self, obj):
        participants = []
        for child in obj.children.all():
            participants.append({
                'id': f"child_{child.id}",
                'name': f"{child.first_name} {child.last_name}",
                'type': 'child'
            })
        for student in obj.students.all():
            participants.append({
                'id': f"student_{student.id}",
                'name': student.user.get_full_name(),
                'type': 'student'
            })
        return participants


class MemoryUploadSerializer(serializers.ModelSerializer):
    file = serializers.CharField()

    class Meta:
        model = Memory
        fields = ['media_type', 'file', 'caption', 'children', 'students']
        
    def create(self, validated_data):
        # uploaded_by should be passed in serializer.save(uploaded_by=...)
        return super().create(validated_data)
