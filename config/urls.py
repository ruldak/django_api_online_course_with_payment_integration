from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from rest_framework.routers import DefaultRouter
from user.views import RegisterView
from courses import views
from payment.views import CreatePayPalOrderView, CapturePayPalOrderView, CreateStrpieCheckoutSessionView, StripeWebhookView

router = DefaultRouter()
router.register(r'cart', views.CartViewSet, basename='cart')

urlpatterns = [
    path('api/', include(router.urls)),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

     # GET endpoints
    path('categories/', views.CategoryListView.as_view(), name='category-list'),
    path('categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('courses/', views.CourseListView.as_view(), name='course-list'),
    path('courses/<int:id>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('instructor/courses/', views.InstructorCourseListView.as_view(), name='instructor-courses'),
    path('course/<int:course_id>/lessons/', views.CourseLessonsListView.as_view(), name='lessons'),

    # CREATE/UPDATE/DELETE endpoints
    path('courses/create/', views.CourseCreateView.as_view(), name='course-create'),
    path('courses/<int:id>/update/', views.CourseUpdateView.as_view(), name='course-update'),
    path('courses/<int:id>/delete/', views.CourseDeleteView.as_view(), name='course-delete'),

    path('cart-items/', views.CartItemListCreateView.as_view(), name='cartitem'),
    path('cart-items/<int:pk>/', views.CartItemDeleteView.as_view(), name='delete-cartitem'),

    path('paypal/create-order/', CreatePayPalOrderView.as_view(), name='paypal-create-order'),
    path('paypal/capture-order/', CapturePayPalOrderView.as_view(), name='paypal-capture-order'),

    path('stripe/create-order/', CreateStrpieCheckoutSessionView.as_view(), name='stripe-create-order'),
    path('stripe/webhooks/', StripeWebhookView.as_view(), name='stripe-webhooks'),
]
