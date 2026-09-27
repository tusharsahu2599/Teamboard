import secrets

from django.contrib.auth.models import User
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import Company


@receiver(pre_save, sender=User)
def remember_user_adding_state(sender, instance, **kwargs):
    # post_save runs after Django clears _state.adding, so capture it first.
    instance._was_adding = instance._state.adding


@receiver(post_save, sender=User)
def create_company_profile(sender, instance, created, **kwargs):
    # _was_adding is instance._state.adding captured in pre_save.
    # post_save clears _state.adding, so `created` is the fallback.
    first_creation = created or getattr(instance, "_was_adding", instance._state.adding)
    if not first_creation:
        return
    if Company.objects.filter(user=instance).exists():
        return
    Company.objects.create(
        user=instance,
        company_name=instance.email,  # overwritten by the register view
        api_key=secrets.token_urlsafe(32),
    )
