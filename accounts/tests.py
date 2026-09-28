from django.contrib.auth.models import User
from django.test import TestCase

from .models import Profile


class ProfileTests(TestCase):
    def test_profile_auto_created(self):
        user = User.objects.create_user(username="u1", password="pass12345")
        self.assertTrue(Profile.objects.filter(user=user).exists())