# Profile Management (step-by-step)

Purpose
- Explain how user profile editing, photo uploads, and brand/client metadata are handled.

Files involved
- [accounts/models.py](accounts/models.py)
- [accounts/forms.py](accounts/forms.py)
- [templates/accounts/profile.html](templates/accounts/profile.html)

Step-by-step implementation
1. Models
   - `UserProfile` (or custom `User`) stores fields like `profile_photo`, `brand_client_name`, `facebook_url`, `instagram_url`, etc.
2. Forms & validation
   - Use `ModelForm` for profile editing; validate URLs and image file types/sizes.
3. Media
   - Configure `MEDIA_ROOT` and `MEDIA_URL` and ensure file uploads are saved to `media/profile_photos/`.
4. Views & URLs
   - Provide authenticated views for `profile` (GET/POST) that update fields and handle file uploads.
5. Templates
   - Show current photo, fields, and a remove/delete option for photos.
6. Tests
   - Add tests that upload small image fixtures and assert database fields and filesystem storage.

Extending
- Add avatars generation, image optimization on upload, and client-specific branding fields.
