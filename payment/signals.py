from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import PaymentTransaction
from enrollments.models import Enrollment

@receiver(post_save, sender=PaymentTransaction)
def create_enrollment_on_payment_success(sender, instance, created, **kwargs):
    if instance.status == 'success':
        cart_items = instance.cart.items.all()

        for item in cart_items:
            Enrollment.objects.get_or_create(
                user=instance.user,
                course=item.course,
                defaults={'payment': instance}
            )
