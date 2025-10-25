from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Enrollment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    payment = models.ForeignKey('payment.PaymentTransaction', on_delete=models.CASCADE, null=True)
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, null=True)
    enrolled_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} enrolled in {self.course.title}"
