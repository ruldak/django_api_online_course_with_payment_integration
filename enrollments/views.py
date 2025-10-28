from rest_framework import generics, permissions
from .models import Enrollment
from .serializers import EnrollmentSerializer

class MyEnrollmentListView(generics.ListAPIView):
    """
    Get all enrollments for the currently logged-in user.
    """
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related('course')
