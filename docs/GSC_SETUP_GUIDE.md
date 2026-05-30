# Google Search Console API Setup Guide

## Step 1: Create a Google Cloud Project

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Click "Create Project" or select an existing project
3. Give it a name like "SEO Optima"
4. Click "Create"

## Step 2: Enable the Google Search Console API

1. In your project, go to **APIs & Services** > **Library**
2. Search for "Google Search Console API"
3. Click on it and click **Enable**

## Step 3: Create OAuth 2.0 Credentials

1. Go to **APIs & Services** > **Credentials**
2. Click **+ CREATE CREDENTIALS** > **OAuth client ID**
3. If prompted, configure the OAuth consent screen first:
   - User Type: **External**
   - App name: **SEO Optima**
   - User support email: your email
   - Developer contact: your email
   - Scopes: Add `https://www.googleapis.com/auth/webmasters.readonly`
   - Test users: Add your Google account email
   - Click **Save and Continue**

4. Back to Create OAuth client ID:
   - Application type: **Web application**
   - Name: **SEO Optima Web Client**
   - Authorized redirect URIs: Add these:
     ```
     http://localhost:8001/dashboard/gsc-callback/
     http://127.0.0.1:8001/dashboard/gsc-callback/
     ```
   - Click **Create**

5. **Download the JSON file** or copy:
   - Client ID
   - Client Secret

## Step 4: Add Credentials to Your Project

Create a `.env` file in your project root (`/Users/nischalgurung/Desktop/Seo-optima v3/`) with:

```env
# Google Search Console API
GOOGLE_CLIENT_ID=your-client-id-here.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret-here
GOOGLE_REDIRECT_URI=http://127.0.0.1:8001/dashboard/gsc-callback/
```

Replace `your-client-id-here` and `your-client-secret-here` with your actual credentials.

## Step 5: Update Django Settings

The code will automatically read from the `.env` file.

## Step 6: Verify Your Site in Search Console

1. Go to [Google Search Console](https://search.google.com/search-console)
2. Add your property (website)
3. Verify ownership using one of the methods
4. Wait for some data to accumulate (usually 48-72 hours)

## Step 7: Test the Connection

1. Start your Django server: `python3 manage.py runserver 8001`
2. Log in to your dashboard
3. Go to **Keywords Finder**
4. Click **Connect Google Search Console**
5. Authorize the app
6. Select your property from the dropdown
7. Analyze keywords!

## Important Notes

- **Scopes**: The app uses `webmasters.readonly` which is read-only access
- **Data Delay**: Search Console data has a 2-3 day delay
- **Limits**: 
  - 200 rows per request (we request 100)
  - 100,000 queries per day per project
- **Testing**: Add your Google account as a test user in OAuth consent screen while the app is in testing mode

## Troubleshooting

### "redirect_uri_mismatch" error
- Make sure the redirect URI in Google Cloud Console exactly matches `http://127.0.0.1:8001/dashboard/gsc-callback/`
- Check for trailing slashes
- Use `127.0.0.1` not `localhost` (or add both)

### "access_denied" error
- Make sure you added yourself as a test user in OAuth consent screen
- The app needs to be in "Testing" mode for now

### No data showing
- Verify your site is added and verified in Search Console
- Check if there's data in Search Console for the past 90 days
- Some new sites may not have data yet

## Production Deployment

When deploying to production:
1. Update redirect URI to your production domain
2. Submit app for verification in Google Cloud Console
3. Update `.env` with production credentials
4. Use HTTPS for redirect URIs
