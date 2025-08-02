from rest_framework import serializers
from .models import Post, PostImage, Category, Tag, Comment

class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = '__all__'


class CommentSerializer(serializers.ModelSerializer):
    post = serializers.ReadOnlyField(source='post.id')
    
    class Meta:
        model = Comment
        fields = '__all__'


class PostImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = PostImage
        fields = ['id', 'image', 'uploaded_at']
        

class PostSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    category = CategorySerializer(read_only=True)
    tags = TagSerializer(many=True, read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    images = PostImageSerializer(many=True, read_only=True)

    class Meta:
        model = Post
        fields = '__all__'

    def update(self, instance, validated_data):
        featured_image = self.context['request'].FILES.get('featured_image')
        if featured_image:
            instance.featured_image = featured_image

        # Optional: handle manual M2M updates here if needed
        tags_data = self.context['request'].data.getlist('tags')
        if tags_data:
            instance.tags.set(tags_data)

        # Update the rest of the fields using validated_data
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
            
        instance.save()
        return instance


