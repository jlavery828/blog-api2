import datetime
import boto3

from botocore.exceptions import NoCredentialsError, ClientError
from django.shortcuts import render, get_object_or_404
from django.conf import settings
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.http import JsonResponse
from rest_framework import generics, viewsets, permissions, serializers, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework.views import APIView

from .models import Post, PostImage, Category, Tag, Comment
from .permissions import IsAuthorOrReadOnly
from .serializers import PostSerializer, PostImageSerializer, CategorySerializer, TagSerializer, CommentSerializer


def test_upload_to_spaces(request):
    now = datetime.datetime.utcnow().isoformat()
    filename = f"test_upload_{now}.txt"
    content = ContentFile(b"This is a test upload to DigitalOcean Spaces.")
    
    try:
        file_path = default_storage.save(filename, content)
        file_url = default_storage.url(file_path)
        return JsonResponse({
            "success": True,
            "file_path": file_path,
            "file_url": file_url
        })
    except Exception as e:
        return JsonResponse({
            "success": False,
            "error": str(e)
        })
    
def test_s3_credentials(request):
    try:
        s3 = boto3.client(
            's3',
            aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            endpoint_url=settings.AWS_S3_ENDPOINT_URL,
        )

        # List first 5 objects in bucket
        objects = s3.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            MaxKeys=5
        )

        # Upload a small test object
        test_key = 'test_s3_credentials.txt'
        s3.put_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=test_key,
            Body=b"This is a test file from Django"
        )

        # # (Optional) Delete test object
        # s3.delete_object(
        #     Bucket=settings.AWS_STORAGE_BUCKET_NAME,
        #     Key=test_key
        # )

        return JsonResponse({
            'success': True,
            'message': 'S3 credentials are valid.',
            'sample_objects': objects.get('Contents', [])
        })

    except NoCredentialsError:
        return JsonResponse({'success': False, 'error': 'No S3 credentials found'})
    except ClientError as e:
        return JsonResponse({'success': False, 'error': str(e)})
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Unexpected error: {str(e)}'})
    


class SimpleTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code != 200:
            return response

        # Instead of setting cookies, just return the tokens
        return Response({
            'access': response.data['access'],
            'refresh': response.data['refresh']
        }, status=status.HTTP_200_OK)
    

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me(request):
    return Response({
        'id': request.user.id,
        'username': request.user.username,
        'email': request.user.email,
    })

@api_view(['POST'])
def logout(request):
    response = Response({'message': 'Logged out successfully'}, status=200)
    response.delete_cookie('access_token', path='/')
    response.delete_cookie('refresh_token', path='/')
    return response
    

class PostViewSet(viewsets.ModelViewSet):
    queryset = Post.objects.all().order_by('-created_at')
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]  # 🔐 Only logged-in users with a valid JWT can post but anyone can read. Also, only the author of a post can edit/delete their posts.

    def perform_create(self, serializer):
        post = serializer.save(author=self.request.user)

        # handle tags
        tags = self.request.data.getlist('tags', [])
        for tag_name in tags:
            tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
            post.tags.add(tag)

        # handle images
        images = self.request.FILES.getlist('images')
        if len(images) > 10:
            raise serializers.ValidationError("Maximum of 10 images allowed.")
        for image in images:
            PostImage.objects.create(post=post, image=image)

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied(f"User: {self.request.user} does not have permission to delete this post.")
        instance.delete()

class PostImageViewSet(viewsets.ModelViewSet):
    queryset = PostImage.objects.all()
    serializer_class = PostImageSerializer

    def create(self, request, *args, **kwargs):
        post_id = request.data.get('post')
        if not post_id:
            return Response({'detail': 'Post ID is required.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            post = Post.objects.get(id=post_id)
        except Post.DoesNotExist:
            return Response({'detail': 'Post not found.'}, status=status.HTTP_404_NOT_FOUND)

        if post.images.count() >= 10:
            return Response({'detail': 'Maximum of 10 images per post allowed.'}, status=status.HTTP_400_BAD_REQUEST)

        return super().create(request, *args, **kwargs)


class PostDetailAPIView(generics.RetrieveAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer

class PostCreateAPIView(generics.CreateAPIView):
    model = Post
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # enables multipart/form-data

    def perform_create(self, serializer):
        print("user: ", self.request.user)
        post = serializer.save(author=self.request.user)

        # Attach tags
        tags_raw = self.request.data.getlist('tags')  # expect multiple "tags=AI" form fields
        for tag_name in tags_raw:
            tag, _ = Tag.objects.get_or_create(name=tag_name.strip())
            post.tags.add(tag)

        # Attach images
        images = self.request.FILES.getlist('images')
        if len(images) > 10:
            raise ValueError("You can only upload up to 10 images.")
        
        for image in images:
            PostImage.objects.create(post=post, image=image)

    def create(self, request, *args, **kwargs):
        print(request.method)
        images = request.FILES.getlist('images')
        if len(images) > 10:
            return Response({'error': 'Maximum 10 images allowed.'}, status=status.HTTP_400_BAD_REQUEST)
        return super().create(request, *args, **kwargs)
    

class PostUpdateAPIView(generics.RetrieveUpdateAPIView):
    queryset = Post.objects.all()
    parser_classes = [MultiPartParser, FormParser]

    def patch(self, request, pk):
        try:
            post = Post.objects.get(pk=pk)
        except Post.DoesNotExist:
            return Response({"error": "Not found"}, status=404)

        serializer = PostSerializer(post, data=request.data, partial=True, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=400)

    # queryset = Post.objects.all()
    # serializer_class = PostSerializer
    # permission_classes = [permissions.IsAuthenticated]

    # # def perform_update(self, serializer):
    # #     post = serializer.instance

    # #     # Optional: restrict updates to post author
    # #     if self.request.user != serializer.instance.author:
    # #         raise permissions.PermissionDenied("You can only edit your own posts.")
    # #     updated_post = serializer.save()

    # #     # Don't clear tags — just add new ones
    # #     submitted_tags = self.request.data.getlist('tags')

    # #     for tag_name in submitted_tags:
    # #         tag_name = tag_name.strip()
    # #         if not tag_name:
    # #             continue
    # #         tag, _ = Tag.objects.get_or_create(name=tag_name)

    # #         if tag not in post.tags.all():
    # #             post.tags.add(tag)

    # #     # Handle new images
    # #     new_images = self.request.FILES.getlist('images')
    # #     if new_images:
    # #         if updated_post.images.count() + len(new_images) > 10:
    # #             raise serializers.ValidationError("Maximum of 10 images allowed.")
    # #         for image in new_images:
    # #             PostImage.objects.create(post=updated_post, image=image)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_queryset(self):
        post_id = self.kwargs.get('post_pk')
        return Comment.objects.filter(post__id=post_id)

    def perform_create(self, serializer):
        post_id = self.kwargs.get('post_pk')
        post = get_object_or_404(Post, id=post_id)
        serializer.save(author=self.request.user, post=post)