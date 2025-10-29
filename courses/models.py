from django.db import models
from django.contrib.auth import get_user_model

from django.db.models import Sum

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    
    def __str__(self):
        return self.name

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    instructor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title


class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()
    order = models.PositiveIntegerField()


class Cart(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='cart'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_price(self):
        return self.items.filter(status='in_cart').aggregate(total_price=Sum('course__price'))['total_price'] or 0


class CartItem(models.Model):
    STATUS_CHOICES = [
        ('in_cart', 'In Cart'),
        ('sold', 'Sold'),
    ]

    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name='items'
    )
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE
    )
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default="in_cart")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['cart', 'course'],
                name='unique_course_in_cart'
            )
        ]
