# SEO Optima Viva Prep Pack - Feature-Wise Documentation

The sections below explain each feature in beginner-friendly terms. Each section includes the purpose, flow, key files, and suggested viva questions.

---

## 1. Authentication and User Account Flow
**What it does:**
- Lets users register, verify email with OTP, log in, and manage profile/settings.

**Why it exists:**
- Ensures only verified users  can access SEO data and reports.

**User flow:**
1. Register with email and password.
2. OTP sent to email.
3. User verifies OTP and account activates.
4. User logs in and reaches dashboard.
5. Optional: Google OAuth sign-in and OTP verification.

**Related files:**
- `accounts/views.py`, `accounts/forms.py`, `accounts/models.py`
- `templates/accounts/login.html`, `register.html`, `verify_otp.html`, `profile.html`, `settings.html`

**Important models/classes/functions:**
- `UserProfile`, `OTP`
- `RegisterView`, `OTPVerifyView`, `GoogleCallbackView`, `SettingsView`, `ProfileView`

**Code flow (step-by-step):**
- `RegisterView` saves inactive user.
- `OTP.create_otp` stores 6-digit code.
- `OTPVerifyView` compares user input vs stored OTP.
- On success: user becomes active and can log in.

**Database fields involved:**
- `OTP.code`, `OTP.expires_at`, `OTP.is_verified`
- `User.is_active`
- `UserProfile` fields (company, photo, social links, defaults)

**External API/package:**
- Google OAuth for sign-in (optional).
- Gmail SMTP for OTP email.

**Error handling:**
- OTP expired or mismatch -> message and retry.
- Missing Google OAuth dependencies -> user sees error.

**How to explain in viva:**
"I used Django’s auth system but extended it with OTP verification. The account is created inactive and only activated after OTP success, which improves security and ensures valid email ownership."

**Possible viva questions and answers:**
- Q: Why use OTP instead of direct signup?  
  A: It verifies ownership of the email before activating the account.
- Q: How do you handle Google login?  
  A: OAuth code is exchanged for a token, then I verify the ID token, create a user if needed, and still require OTP.

---

## 2. Dashboard Home
**What it does:**
- Shows an overview of recent activities, stats, and charts.

**Why it exists:**
- Gives quick insight into SEO progress and history.

**User flow:**
1. User logs in.
2. Redirected to dashboard home.
3. Recent analyses and charts are displayed.

**Related files:**
- `dashboard/views.py` (`dashboard_home`)
- `templates/dashboard/index.html`

**Important functions:**
- `_build_recent_section` and `_build_recent_item`

**Code flow:**
- Query recent `PageSpeedAnalysis`, `HeaderAnalysis`, `ImageAltAnalysis`, `KeywordAnalysis`, `PDFReport`.
- Build chart data for week/month/year.
- Render dashboard template.

**Database tables:**
- All analysis models + PDFReport

**External APIs:**
- None (reads from DB only)

**Error handling:**
- No heavy error handling needed because data is already stored.

**How to explain in viva:**
"Dashboard is an aggregation view. It does not fetch new SEO data; it summarizes existing records for quick decision-making."

**Viva Q&A:**
- Q: Why not call APIs directly on dashboard?  
  A: That would be slow and expensive; it is better to reuse stored results.

---

## 3. PageSpeed Insights Analysis
**What it does:**
- Uses Google PageSpeed Insights API to analyze performance, accessibility, best practices, and SEO scores.

**Why it exists:**
- Performance strongly affects search ranking and user experience.

**User flow:**
1. User enters a URL and selects mobile/desktop.
2. System fetches data from Google API.
3. Results stored in database and shown in UI.

**Related files:**
- `dashboard/views.py` (`page_speed_insights`, `analysis_detail`)
- `dashboard/services/pagespeed.py`
- `templates/dashboard/page_speed_insights.html`, `analysis_detail.html`

**Important models:**
- `PageSpeedAnalysis`

**Code flow:**
1. Form validates URL.
2. `fetch_pagespeed_data` calls Google API.
3. `parse_pagespeed_response` extracts scores/metrics.
4. View stores result in DB.
5. Detail page uses stored `full_response`.

**Database fields:**
- `performance_score`, `seo_score`, `metrics`, `full_response`

**External API:**
- Google PageSpeed Insights API

**Error handling:**
- Invalid API key -> user sees clear message.
- Timeout -> handled with error message.

**How to explain in viva:**
"This feature is a classic API integration. I fetch JSON from Google, parse it, store scores, and later render them."

**Possible viva questions:**
- Q: Why save full response?  
  A: It allows detail pages without re-calling the API.

---

## 4. Google Search Console Keyword Analysis
**What it does:**
- Fetches real keyword ranking data from GSC.

**Why it exists:**
- Keywords show actual search performance, not just on-page metrics.

**User flow:**
1. User connects GSC via OAuth.
2. Properties are fetched and displayed.
3. User selects a property or enters URL.
4. Keywords are fetched and stored.

**Related files:**
- `dashboard/views.py` (`connect_gsc`, `gsc_callback`, `keywords_finder`)
- `dashboard/services/keyword_extractor.py`
- `templates/dashboard/keywords_finder.html`, `keywords_list.html`, `keywords_detail.html`

**Important models:**
- `GSCConnection`, `KeywordAnalysis`

**Code flow:**
1. OAuth flow stores credentials in DB.
2. `fetch_gsc_keywords` calls Search Console API.
3. Data is aggregated by keyword and stored.
4. UI shows stats and keyword list.

**Database fields:**
- `GSCConnection.credentials`, `GSCConnection.properties`
- `KeywordAnalysis.keywords_data`, `avg_position`, `total_volume`

**External API:**
- Google Search Console API

**Error handling:**
- Auth revoked -> connection set to inactive and user prompted to reconnect.
- Missing data -> shows clear error message.

**How to explain in viva:**
"This feature is real SEO data. I use OAuth to access Search Console and pull query+page data so each keyword keeps its correct landing URL."

**Possible viva questions:**
- Q: Why use dimensions ['query','page']?  
  A: To map each keyword to the exact ranked page instead of guessing.
- Q: How do you handle token expiry?  
  A: Detect auth errors and mark the connection inactive so the user reconnects.

---

## 5. Header Extraction
**What it does:**
- Extracts H1-H6 tags from a page and shows structure.

**Why it exists:**
- Good heading hierarchy improves SEO and readability.

**User flow:**
1. User enters URL.
2. HTML is fetched and parsed.
3. Header list and counts are displayed.

**Related files:**
- `dashboard/views.py` (`extract_headers_view`, `header_analysis_detail`)
- `dashboard/services/header_extractor.py`
- `templates/dashboard/extract_headers.html`, `header_analysis_detail.html`

**Important models:**
- `HeaderAnalysis`

**Code flow:**
1. View calls `extract_headers`.
2. `get_header_hierarchy` counts H1/H2/H3.
3. Results saved in DB and displayed.

**Database fields:**
- `headers_data`, `h1_count`, `h2_count`, `h3_count`

**External API/package:**
- `requests`, `BeautifulSoup`

**Error handling:**
- Network errors and parse failures are shown in alerts.

**How to explain in viva:**
"This is a pure on-page SEO check. I parse HTML and summarize the header structure to find missing or multiple H1 tags."

**Possible viva questions:**
- Q: Why is one H1 important?  
  A: It signals the main topic to search engines.

---

## 6. Image and Alt Text Checker
**What it does:**
- Extracts all images and checks if alt text exists.

**Why it exists:**
- Alt text improves accessibility and image SEO.

**User flow:**
1. User enters URL.
2. Images are extracted with alt text.
3. Results stored and displayed.

**Related files:**
- `dashboard/views.py` (`image_alt_finder`, `image_alt_detail`)
- `dashboard/services/image_extractor.py`
- `templates/dashboard/image_alt_finder.html`, `image_alt_detail.html`

**Important models:**
- `ImageAltAnalysis`

**Code flow:**
1. View calls `extract_images`.
2. `get_image_stats` counts missing alt text.
3. Store results in database.

**Database fields:**
- `images_data`, `images_with_alt`, `images_without_alt`

**External API/package:**
- `requests`, `BeautifulSoup`

**Error handling:**
- Request failures show error message.

**How to explain in viva:**
"This checks image accessibility and SEO. It flags missing alt text, which is a common SEO issue."

---

## 7. PDF Report Generation
**What it does:**
- Builds a PDF report combining selected analysis data.

**Why it exists:**
- Allows exporting results for sharing or documentation.

**User flow:**
1. User chooses report type and analyses.
2. System generates a PDF file.
3. PDF is stored and can be downloaded.

**Related files:**
- `dashboard/pdf_report_views.py`
- `dashboard/services/pdf_generator.py`
- `templates/dashboard/generate_pdf_report.html`, `pdf_reports_list.html`, `pdf_report_detail.html`

**Important models:**
- `PDFReport`

**Code flow:**
1. View validates that at least one analysis is selected.
2. `generate_basic_report` creates PDF in memory.
3. Report saved and returned for download.

**Database fields:**
- `pdf_file`, `report_type`, `pagespeed_analysis`, `keyword_analysis`, `image_analysis`

**External package:**
- ReportLab

**Error handling:**
- Catches exceptions and shows error message.

**How to explain in viva:**
"The PDF feature turns stored SEO results into a professional report. It uses ReportLab to format tables and recommendations."

---

## 8. Admin/Database Management
**What it does:**
- Provides admin UI to manage analyses and users.

**Why it exists:**
- Admin can inspect stored records for debugging and maintenance.

**Related files:**
- `dashboard/admin.py`, `accounts/admin.py`

**Important models:**
- All analysis models and user profiles.

**How to explain in viva:**
"Admin is Django’s built-in dashboard. I registered my models so I can view and manage stored SEO analyses."

---

## 9. Testing
**What it does:**
- Verifies keyword extraction and dashboard rendering.

**Related files:**
- `dashboard/tests.py`
- `accounts/tests.py`
- `test_email.py`, `test_property_matching.py`

**How to explain in viva:**
"I included unit and integration tests for key logic like keyword aggregation and profile updates, plus scripts for SMTP and GSC property matching."

---

# Short Code Snippets with Explanation

### GSC keyword aggregation (dashboard/services/keyword_extractor.py)
```python
keyword_aggregates = {}
for row in rows:
    keys = row.get('keys', [])
    if len(keys) < 2:
        continue
    keyword = keys[0]
    ranked_url = keys[1]
```
**Line-by-line:**
- Creates a dictionary to aggregate keywords.
- Loops through rows from GSC.
- Checks row has both query and page keys.
- Extracts keyword and URL per row.

### PDF generation call (dashboard/pdf_report_views.py)
```python
pdf_file = generate_basic_report(
    user=request.user,
    title=title,
    pagespeed_analysis=pagespeed_analysis,
    keyword_analysis=keyword_analysis,
    image_analysis=image_analysis,
    headers_data=headers_data
)
```
**Line-by-line:**
- Calls PDF generator with selected analysis objects.
- Returns a file-like object saved into the `PDFReport` model.

