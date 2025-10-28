from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.routers import DefaultRouter
from user.views import RegisterView
from courses import views
from payment.views import CreatePayPalOrderView, CapturePayPalOrderView, PayPalWebhookView, CreateStrpieCheckoutSessionView, StripeWebhookView
from enrollments.views import MyEnrollmentListView

router = DefaultRouter()
router.register(r'cart', views.CartViewSet, basename='cart')

urlpatterns = [
    # API DOCS
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('api/', include(router.urls)),

    path('api/register/', RegisterView.as_view(), name='register'),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

     # GET endpoints
    path('api/categories/', views.CategoryListView.as_view(), name='category-list'),
    path('api/categories/create/', views.CategoryCreateView.as_view(), name='category-create'),
    path('api/courses/', views.CourseListView.as_view(), name='course-list'),
    path('api/courses/<int:id>/', views.CourseDetailView.as_view(), name='course-detail'),
    path('api/instructor/courses/', views.InstructorCourseListView.as_view(), name='instructor-courses'),
    path('api/courses/<int:course_id>/lessons/', views.CourseLessonsListView.as_view(), name='lessons'),
    path('api/my-enrollments/', MyEnrollmentListView.as_view(), name='my-enrollments'),

    # CREATE/UPDATE/DELETE endpoints
    path('api/courses/create/', views.CourseCreateView.as_view(), name='course-create'),
    path('api/courses/<int:id>/update/', views.CourseUpdateView.as_view(), name='course-update'),
    path('api/courses/<int:id>/delete/', views.CourseDeleteView.as_view(), name='course-delete'),

    path('api/cart-items/', views.CartItemListCreateView.as_view(), name='cartitem'),
    path('api/cart-items/<int:pk>/', views.CartItemDeleteView.as_view(), name='delete-cartitem'),

    path('api/paypal/create-order/', CreatePayPalOrderView.as_view(), name='paypal-create-order'),
    path('api/paypal/capture-order/', CapturePayPalOrderView.as_view(), name='paypal-capture-order'),
    path('api/paypal/webhooks/', PayPalWebhookView.as_view(), name='paypal-webhooks'),

    path('api/stripe/create-order/', CreateStrpieCheckoutSessionView.as_view(), name='stripe-create-order'),
    path('api/stripe/webhooks/', StripeWebhookView.as_view(), name='stripe-webhooks'),
]
