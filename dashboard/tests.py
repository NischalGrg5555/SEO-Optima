from unittest import TestCase
from unittest.mock import MagicMock, patch

from dashboard.services.keyword_extractor import fetch_gsc_keywords


class FetchGSCKeywordsTests(TestCase):
    @patch('dashboard.services.keyword_extractor.build')
    @patch('dashboard.services.keyword_extractor.Credentials')
    def test_uses_page_dimension_and_returns_real_row_url(self, mock_credentials_cls, mock_build):
        credentials = MagicMock()
        credentials.expired = False
        credentials.refresh_token = 'refresh-token'
        credentials.valid = True
        mock_credentials_cls.return_value = credentials

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

    @patch('dashboard.services.keyword_extractor.build')
    @patch('dashboard.services.keyword_extractor.Credentials')
    def test_aggregates_same_keyword_and_keeps_highest_impression_page(self, mock_credentials_cls, mock_build):
        credentials = MagicMock()
        credentials.expired = False
        credentials.refresh_token = 'refresh-token'
        credentials.valid = True
        mock_credentials_cls.return_value = credentials

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
