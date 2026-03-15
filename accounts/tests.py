from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import UserProfile


class ProfileViewTests(TestCase):
	def setUp(self):
		self.user = User.objects.create_user(
			username='profile@example.com',
			email='profile@example.com',
			password='strong-password-123',
			first_name='Nischal',
		)

	def test_profile_created_automatically(self):
		self.assertTrue(UserProfile.objects.filter(user=self.user).exists())

	def test_profile_page_requires_login(self):
		response = self.client.get(reverse('accounts:profile'))
		self.assertEqual(response.status_code, 302)

	def test_profile_page_updates_user_and_profile(self):
		self.client.login(username='profile@example.com', password='strong-password-123')
		response = self.client.post(reverse('accounts:profile'), {
			'first_name': 'Nischal',
			'last_name': 'Gurung',
			'email': 'profile@example.com',
			'job_title': 'SEO Analyst',
			'phone': '+9779800000000',
			'bio': 'Working on search visibility and reporting.',
		})

		self.assertRedirects(response, reverse('accounts:profile'))

		self.user.refresh_from_db()
		profile = self.user.profile
		self.assertEqual(self.user.first_name, 'Nischal')
		self.assertEqual(self.user.last_name, 'Gurung')
		self.assertEqual(profile.job_title, 'SEO Analyst')
