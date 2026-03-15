from django.contrib.auth.models import User
from django.core.files.uploadedfile import SimpleUploadedFile
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
		avatar = SimpleUploadedFile(
			'avatar.gif',
			(
				b'GIF89a\x01\x00\x01\x00\x80\x00\x00\x00\x00\x00'
				b'\xff\xff\xff!\xf9\x04\x01\x00\x00\x00\x00,\x00\x00\x00\x00'
				b'\x01\x00\x01\x00\x00\x02\x02D\x01\x00;'
			),
			content_type='image/gif',
		)
		response = self.client.post(reverse('accounts:profile'), {
			'profile_photo': avatar,
			'facebook_url': 'https://www.facebook.com/seooptima',
			'x_url': 'https://x.com/seooptima',
			'linkedin_url': 'https://www.linkedin.com/company/seooptima',
			'instagram_url': 'https://www.instagram.com/seooptima',
			'first_name': 'Nischal Gurung',
			'email': 'profile@example.com',
			'company': 'SEO Optima',
			'job_title': 'SEO Analyst',
			'bio': 'Working on search visibility and reporting.',
		})

		self.assertRedirects(response, reverse('accounts:profile'))

		self.user.refresh_from_db()
		profile = self.user.profile
		self.assertEqual(self.user.first_name, 'Nischal Gurung')
		self.assertEqual(self.user.last_name, '')
		self.assertEqual(profile.company, 'SEO Optima')
		self.assertEqual(profile.job_title, 'SEO Analyst')
		self.assertEqual(profile.facebook_url, 'https://www.facebook.com/seooptima')
		self.assertTrue(bool(profile.profile_photo))

	def test_profile_page_renders_saved_social_links(self):
		self.user.profile.facebook_url = 'https://www.facebook.com/seooptima'
		self.user.profile.x_url = 'https://x.com/seooptima'
		self.user.profile.linkedin_url = 'https://www.linkedin.com/company/seooptima'
		self.user.profile.instagram_url = 'https://www.instagram.com/seooptima'
		self.user.profile.save()

		self.client.login(username='profile@example.com', password='strong-password-123')
		response = self.client.get(reverse('accounts:profile'))

		self.assertContains(response, 'https://www.facebook.com/seooptima')
		self.assertContains(response, 'https://x.com/seooptima')
		self.assertContains(response, 'https://www.linkedin.com/company/seooptima')
		self.assertContains(response, 'https://www.instagram.com/seooptima')
