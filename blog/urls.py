from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested.routers import NestedDefaultRouter
from .views import PostViewSet, PostImageViewSet, PostCreateAPIView, PostUpdateAPIView, PostDetailAPIView, CategoryViewSet, TagViewSet, CommentViewSet, me, logout

router = DefaultRouter()
router.register(r'posts', PostViewSet, basename='posts')
router.register(r'categories', CategoryViewSet)
router.register(r'tags', TagViewSet)
router.register(r'images', PostImageViewSet)
router.register(r'comments', CommentViewSet)

# Nested router: /posts/<post_id>/comments/
posts_router = NestedDefaultRouter(router, r'posts', lookup='post')
posts_router.register(r'images', PostImageViewSet, basename='post-images')
posts_router.register(r'comments', CommentViewSet, basename='post-comments')

urlpatterns = router.urls + posts_router.urls

urlpatterns += [
    path('me/', me),
    path('logout/', logout),
    path('posts/<int:pk>/', PostDetailAPIView.as_view(), name="post-detail"),
    path('post/create/', PostCreateAPIView.as_view(), name='post-create'),
    path('post/<int:pk>/update/', PostUpdateAPIView.as_view(), name='post-update'),
]