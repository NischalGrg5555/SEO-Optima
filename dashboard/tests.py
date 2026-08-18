from unittest import TestCase as UnitTestCase
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase as DjangoTestCase
from django.urls import reverse

from dashboard.services.keyword_extractor import fetch_gsc_keywords


class FetchGSCKeywordsTests(UnitTestCase):
    @patch('dashboard.services.keyword_extractor._load_google_clients')
    def test_uses_page_dimension_and_returns_real_row_url(self, mock_load_clients):
        mock_credentials_cls = MagicMock()
        mock_build = MagicMock()
        mock_request_cls = MagicMock()
        mock_refresh_error_cls = Exception

        credentials = MagicMock()
        credentials.expired = False
        credentials.refresh_token = 'refresh-token'
        credentials.valid = True
        mock_credentials_cls.from_authorized_user_info.return_value = credentials

        mock_load_clients.return_value = (
            mock_build,
            mock_credentials_cls,
            mock_request_cls,
            mock_refresh_error_cls,
        )

        api_response = {
            'rows': [
                {
                    'keys': ['igcse meaning', 'https://homeschool.asia/faqs/what-is-igcse/'],
                    'clicks': 0,
                    'impressions': 631,
                    'ctr': 0.0,
                    'position': 5.9,
                }
            ]
        }

        query_mock = MagicMock()
        query_mock.execute.return_value = api_response

        searchanalytics_mock = MagicMock()
        searchanalytics_mock.query.return_value = query_mock

        service_mock = MagicMock()
        service_mock.searchanalytics.return_value = searchanalytics_mock
        mock_build.return_value = service_mock

        result = fetch_gsc_keywords(
            'sc-domain:homeschool.asia',
            credentials_dict={
                'token': 'token',
                'refresh_token': 'refresh-token',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': 'client-id',
                'client_secret': 'client-secret',
                'scopes': ['https://www.googleapis.com/auth/webmasters.readonly'],
            },
            properties_list=['sc-domain:homeschool.asia'],
            days=7,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['keyword'], 'igcse meaning')
        self.assertEqual(result[0]['url'], 'https://homeschool.asia/faqs/what-is-igcse/')

        _, kwargs = searchanalytics_mock.query.call_args
        self.assertEqual(kwargs['body']['dimensions'], ['query', 'page'])

    @patch('dashboard.services.keyword_extractor._load_google_clients')
    def test_aggregates_same_keyword_and_keeps_highest_impression_page(self, mock_load_clients):
        mock_credentials_cls = MagicMock()
        mock_build = MagicMock()
        mock_request_cls = MagicMock()
        mock_refresh_error_cls = Exception

        credentials = MagicMock()
        credentials.expired = False
        credentials.refresh_token = 'refresh-token'
        credentials.valid = True
        mock_credentials_cls.from_authorized_user_info.return_value = credentials

        mock_load_clients.return_value = (
            mock_build,
            mock_credentials_cls,
            mock_request_cls,
            mock_refresh_error_cls,
        )

        api_response = {
            'rows': [
                {
                    'keys': ['igcse meaning', 'https://homeschool.asia/faqs/what-is-igcse/'],
                    'clicks': 8,
                    'impressions': 500,
                    'ctr': 0.016,
                    'position': 5.0,
                },
                {
                    'keys': ['igcse meaning', 'https://homeschool.asia/blogs/what-is-igcse-complete-guide/'],
                    'clicks': 2,
                    'impressions': 131,
                    'ctr': 0.015,
                    'position': 9.0,
                },
            ]
        }

        query_mock = MagicMock()
        query_mock.execute.return_value = api_response

        searchanalytics_mock = MagicMock()
        searchanalytics_mock.query.return_value = query_mock

        service_mock = MagicMock()
        service_mock.searchanalytics.return_value = searchanalytics_mock
        mock_build.return_value = service_mock

        result = fetch_gsc_keywords(
            'sc-domain:homeschool.asia',
            credentials_dict={
                'token': 'token',
                'refresh_token': 'refresh-token',
                'token_uri': 'https://oauth2.googleapis.com/token',
                'client_id': 'client-id',
                'client_secret': 'client-secret',
                'scopes': ['https://www.googleapis.com/auth/webmasters.readonly'],
            },
            properties_list=['sc-domain:homeschool.asia'],
            days=7,
        )

        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['keyword'], 'igcse meaning')
        self.assertEqual(result[0]['volume'], 631)
        self.assertEqual(result[0]['clicks'], 10)
        self.assertEqual(result[0]['url'], 'https://homeschool.asia/faqs/what-is-igcse/')


class DashboardHomeRecentSectionsTests(DjangoTestCase):
    def test_dashboard_home_renders_feature_recent_sections(self):
        user = User.objects.create_user(username='dashboard-user', password='password123')
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:home'))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Recent Activity')
        self.assertContains(response, 'PageSpeed Insights')
        self.assertContains(response, 'Header Analysis')
        self.assertContains(response, 'Image Alt Analysis')
        self.assertContains(response, 'Keyword Analysis')
        self.assertContains(response, 'PDF Reports')


class AIReadinessExtractorTests(UnitTestCase):
    @patch('dashboard.services.ai_search_extractor.requests.get')
    def test_analyze_ai_readiness_parses_html_correctly(self, mock_get):
        sample_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <script type="application/ld+json">
            {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": "What is AEO Optimization?",
                "author": {"@type": "Person", "name": "SEO Expert"}
            }
            </script>
        </head>
        <body>
            <h1>Generative Engine Optimization Guide</h1>
            <h2>What is Answer Engine Optimization?</h2>
            <p>Answer Engine Optimization (AEO) is the strategic process of structuring and refining website content so that AI search engines and RAG retrieval pipelines can easily parse, extract, and cite direct answers for user queries across AI assistants.</p>
            <ol>
                <li>Structure content with clear question headings.</li>
                <li>Add 40 to 80 word direct answer paragraphs.</li>
                <li>Include JSON-LD schema metadata.</li>
            </ol>
            <table>
                <thead>
                    <tr><th>Metric</th><th>Target</th></tr>
                </thead>
                <tbody>
                    <tr><td>Direct Answer Length</td><td>40-80 words</td></tr>
                </tbody>
            </table>
            <div class="author-bio">Written by Jane Doe on 2026-08-18</div>
        </body>
        </html>
        """
        main_resp = MagicMock()
        main_resp.status_code = 200
        main_resp.text = sample_html

        robots_resp = MagicMock()
        robots_resp.status_code = 200
        robots_txt = "User-agent: *\nAllow: /\n"
        robots_resp.text = robots_txt

        mock_get.side_effect = [main_resp, robots_resp]

        from dashboard.services.ai_search_extractor import analyze_ai_readiness
        result = analyze_ai_readiness("https://example.com/aeo-guide")

        self.assertIn('overall_score', result)
        self.assertGreaterEqual(result['overall_score'], 70)
        self.assertEqual(result['audit_results']['question_headings_count'], 1)
        self.assertEqual(result['audit_results']['optimal_passages_count'], 1)
        self.assertIn('Article', result['audit_results']['entity']['detected_schemas'])
        self.assertEqual(result['audit_results']['structure']['ordered_lists'], 1)
        self.assertEqual(result['audit_results']['structure']['table_count'], 1)


class AIReadinessViewTests(DjangoTestCase):
    def test_ai_search_overview_and_audit_flow(self):
        user = User.objects.create_user(username='ai-user', password='password123')
        self.client.force_login(user)

        response = self.client.get(reverse('dashboard:ai_search_overview'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'AI Search Readiness & Optimization')

        # Run mock audit view
        with patch('dashboard.views.analyze_ai_readiness') as mock_extractor:
            mock_extractor.return_value = {
                'overall_score': 85,
                'answerability_score': 90,
                'structure_score': 80,
                'entity_score': 85,
                'technical_score': 100,
                'trust_score': 70,
                'audit_results': {'total_words': 500, 'technical': {'blocked_bots_count': 0}},
                'recommendations': []
            }
            post_response = self.client.post(reverse('dashboard:ai_readiness_audit'), {'url': 'https://example.com/test-ai'})
            
            # Should redirect to detail view
            self.assertEqual(post_response.status_code, 302)
            
            from dashboard.models import AIReadinessAnalysis
            analysis = AIReadinessAnalysis.objects.get(url='https://example.com/test-ai')
            self.assertEqual(analysis.overall_score, 85)

    def test_step2_question_research_and_citation_opportunities_views(self):
        user = User.objects.create_user(username='step2-user', password='password123')
        self.client.force_login(user)

        # Question Research View
        q_response = self.client.get(reverse('dashboard:ai_question_research') + '?seed=page+speed')
        self.assertEqual(q_response.status_code, 200)
        self.assertContains(q_response, 'AI Search Question & Intent Generator')
        self.assertContains(q_response, 'page speed')

        # Citation Opportunities View
        opp_response = self.client.get(reverse('dashboard:ai_citation_opportunities'))
        self.assertEqual(opp_response.status_code, 200)
        self.assertContains(opp_response, 'AI Citation Opportunity Finder')


