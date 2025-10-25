from rest_framework import generics, permissions, status, filters, viewsets, serializers
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from django.db import models, IntegrityError
from .models import Course, Lesson, Category, Cart, CartItem
from .serializers import CourseSerializer, CategorySerializer, CartItemSerializer, CartSerializer, CreateCourseSerializer, LessonSerializer
from enrollments.models import Enrollment
from rest_framework.exceptions import PermissionDenied

# ===== GET VIEWS =====

class CategoryListView(generics.ListAPIView):
    """Get all categories"""
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

# temporary view, remove this later
class CategoryCreateView(generics.CreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.AllowAny]

class CourseListView(generics.ListAPIView):
    """Get all courses"""
    queryset = Course.objects.all().select_related('instructor')
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    filter_backends = [filters.OrderingFilter, DjangoFilterBackend]
    filterset_fields = ['category']
    ordering_fields = ['created_at']

class CourseDetailView(generics.RetrieveAPIView):
    """Get single course detail"""
    queryset = Course.objects.all().select_related('instructor')
    serializer_class = CourseSerializer
    permission_classes = [permissions.AllowAny]
    lookup_field = 'id'

class InstructorCourseListView(generics.ListAPIView):
    """Get courses by logged-in instructor"""
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

class CourseLessonsListView(generics.ListAPIView):
    serializer_class = LessonSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        course_id = self.kwargs['course_id']
        is_granted = Enrollment.objects.filter(user=self.request.user, course=course_id).exists()

        if not is_granted:
            raise PermissionDenied("You don't have permission to access this content.")

        return Lesson.objects.filter(course=course_id).order_by('order')

# ===== CREATE/UPDATE VIEWS =====
class CourseCreateView(generics.CreateAPIView):
    """Create new course"""
    queryset = Course.objects.all()
    serializer_class = CreateCourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(instructor=self.request.user)

class CourseUpdateView(generics.UpdateAPIView):
    """Update course - only by instructor"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)

class CourseDeleteView(generics.DestroyAPIView):
    """Delete course - only by instructor"""
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

    def get_queryset(self):
        return Course.objects.filter(instructor=self.request.user)


class CartViewSet(viewsets.ReadOnlyModelViewSet):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CartSerializer

    def get_queryset(self):
        return Cart.objects.filter(user=self.request.user)


class CartItemListCreateView(generics.ListCreateAPIView):
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart=self.request.user.cart)

    def perform_create(self, serializer):
        try:
            serializer.save(cart=self.request.user.cart)
        except IntegrityError:
            raise serializers.ValidationError({
                'course': 'Course ini sudah ada di keranjang belanja.'
            })

class CartItemDeleteView(generics.DestroyAPIView):
    queryset = CartItem.objects.all()
    serializer_class = CartItemSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CartItem.objects.filter(cart=self.request.user.cart)
