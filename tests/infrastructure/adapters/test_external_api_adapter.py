import unittest
from unittest.mock import patch, Mock, call # call is useful for checking call_args
import requests # For requests.auth.HTTPBasicAuth and requests.exceptions

from src.infrastructure.adapters.external_api_adapter import ExternalApiAdapter, ExternalApiError
from src.config import ( # We might need to patch these if they are directly accessed and not placeholders
    OIL_PRICE_API_URL, OIL_PRICE_API_KEY,
    EXCHANGE_RATE_API_URL,
    PRODUCTION_DATA_API_URL, PRODUCTION_API_KEY,
    ODATA_PRODUCTION_DATA_API_URL, ODATA_API_USERNAME, ODATA_API_PASSWORD
)

class TestExternalApiAdapter(unittest.TestCase):

    def setUp(self):
        """
        Common setup for tests.
        We can initialize the adapter here if config patching is consistent.
        However, since some tests patch config values at the method level,
        it might be cleaner to instantiate the adapter within each test
        or after specific patches are applied.
        """
        # Example of how you might patch globally if needed, but instructions suggest per-test patching for OData
        # self.patcher_odata_url = patch('src.infrastructure.adapters.external_api_adapter.ODATA_PRODUCTION_DATA_API_URL', "http://fakeodata.com")
        # self.mock_odata_url = self.patcher_odata_url.start()
        # self.addCleanup(self.patcher_odata_url.stop)
        pass # Adapter will be created in tests after specific patches

    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_PRODUCTION_DATA_API_URL', "http://fakeodata.com")
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_USERNAME', "testuser")
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_PASSWORD', "testpass")
    @patch('requests.get')
    def test_fetch_data_basic_auth_success(self, mock_requests_get, mock_pass, mock_user, mock_url):
        """
        Test fetch_data with successful Basic Authentication.
        """
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = [{"id": 1, "data": "value"}]
        mock_requests_get.return_value = mock_response

        adapter = ExternalApiAdapter() # Initialize after patches
        result = adapter.fetch_data("odata_production_data")

        expected_url = "http://fakeodata.com"
        mock_requests_get.assert_called_once_with(
            expected_url,
            params=None,
            headers={"Accept": "application/json"},
            auth=requests.auth.HTTPBasicAuth("testuser", "testpass"),
            timeout=10
        )
        self.assertEqual(result, [{"id": 1, "data": "value"}])

    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_PRODUCTION_DATA_API_URL', "http://fakeodata.com")
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_USERNAME', "YOUR_USERNAME_PLACEHOLDER") # Placeholder
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_PASSWORD', "testpass")
    def test_fetch_data_basic_auth_missing_username(self, mock_pass, mock_user, mock_url):
        """
        Test fetch_data with Basic Auth fails if username is a placeholder.
        """
        adapter = ExternalApiAdapter()
        with self.assertRaisesRegex(ExternalApiError, "Username or password for Basic Auth in 'odata_production_data' is missing or is a placeholder."):
            adapter.fetch_data("odata_production_data")

    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_PRODUCTION_DATA_API_URL', "http://fakeodata.com")
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_USERNAME', "testuser")
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_PASSWORD', None) # Password is None
    def test_fetch_data_basic_auth_missing_password(self, mock_pass, mock_user, mock_url):
        """
        Test fetch_data with Basic Auth fails if password is None.
        """
        adapter = ExternalApiAdapter()
        with self.assertRaisesRegex(ExternalApiError, "Username or password for Basic Auth in 'odata_production_data' is missing or is a placeholder."):
            adapter.fetch_data("odata_production_data")

    # Patching production_data specific config for this test
    @patch('src.infrastructure.adapters.external_api_adapter.PRODUCTION_DATA_API_URL', "http://fakeproduction.com/api")
    @patch('src.infrastructure.adapters.external_api_adapter.PRODUCTION_API_KEY', "testkey123")
    @patch('requests.get')
    def test_fetch_data_api_key_auth_still_works(self, mock_requests_get, mock_key, mock_url):
        """
        Test that existing API key authentication still works for other sources.
        """
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = [{"prod_id": 100, "value": "prod_data"}]
        mock_requests_get.return_value = mock_response

        adapter = ExternalApiAdapter()
        result = adapter.fetch_data("production_data") # Use a source configured for API key

        expected_url = "http://fakeproduction.com/api"
        mock_requests_get.assert_called_once_with(
            expected_url,
            params=None,
            headers={
                "Accept": "application/json",
                "X-API-Key": "X-API-Key testkey123" # As per adapter logic for this source
            },
            auth=None, # Explicitly check that basic auth is not used
            timeout=10
        )
        self.assertEqual(result, [{"prod_id": 100, "value": "prod_data"}])
        
    # Test for default Bearer token behavior if key_header_template is not specific
    @patch('src.infrastructure.adapters.external_api_adapter.OIL_PRICE_API_URL', "http://fakeoil.com/api")
    @patch('src.infrastructure.adapters.external_api_adapter.OIL_PRICE_API_KEY', "oilkey456")
    @patch('requests.get')
    def test_fetch_data_api_key_auth_bearer_token(self, mock_requests_get, mock_key, mock_url):
        """
        Test that API key authentication with default Bearer token works.
        """
        mock_response = Mock(status_code=200)
        mock_response.json.return_value = [{"price_id": 200, "value": "oil_price"}]
        mock_requests_get.return_value = mock_response

        adapter = ExternalApiAdapter()
        result = adapter.fetch_data("oil_price")

        expected_url = "http://fakeoil.com/api"
        mock_requests_get.assert_called_once_with(
            expected_url,
            params=None,
            headers={
                "Accept": "application/json",
                "Authorization": "Bearer oilkey456"
            },
            auth=None,
            timeout=10
        )
        self.assertEqual(result, [{"price_id": 200, "value": "oil_price"}])


    @patch.object(ExternalApiAdapter, 'fetch_data', autospec=True) # autospec ensures signature matching
    def test_fetch_production_data_monthly_success(self, mock_fetch_data):
        """
        Test fetch_production_data_monthly successfully calls fetch_data.
        """
        expected_result = [{"month_data": "some_value"}]
        mock_fetch_data.return_value = expected_result

        adapter = ExternalApiAdapter()
        year, month = 2023, 10
        result = adapter.fetch_production_data_monthly(year, month, params={"extra_param": "foo"})

        mock_fetch_data.assert_called_once_with(
            adapter, # self argument
            "odata_production_data",
            params={"year": year, "month": month, "extra_param": "foo"}
        )
        self.assertEqual(result, expected_result)

    @patch.object(ExternalApiAdapter, 'fetch_data', autospec=True)
    def test_fetch_production_data_monthly_propagates_error(self, mock_fetch_data):
        """
        Test that fetch_production_data_monthly propagates ExternalApiError from fetch_data.
        """
        mock_fetch_data.side_effect = ExternalApiError("API failed", status_code=500)

        adapter = ExternalApiAdapter()
        year, month = 2023, 11

        with self.assertRaisesRegex(ExternalApiError, "API failed"):
            adapter.fetch_production_data_monthly(year, month)
        
        mock_fetch_data.assert_called_once_with(
            adapter,
            "odata_production_data",
            params={"year": year, "month": month}
        )

    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_PRODUCTION_DATA_API_URL', "http://actual-url.com") # Non-placeholder URL
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_USERNAME', "user")
    @patch('src.infrastructure.adapters.external_api_adapter.ODATA_API_PASSWORD', "pass")
    @patch('requests.get')
    def test_fetch_data_basic_auth_http_error(self, mock_requests_get, mock_pass, mock_user, mock_url):
        """Test that HTTP errors from requests.get are wrapped in ExternalApiError."""
        mock_response = Mock(status_code=404)
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(response=mock_response)
        mock_response.text = "Not Found"
        mock_requests_get.return_value = mock_response

        adapter = ExternalApiAdapter()
        with self.assertRaises(ExternalApiError) as cm:
            adapter.fetch_data("odata_production_data")
        
        self.assertEqual(cm.exception.status_code, 404)
        self.assertIn("failed with status 404", cm.exception.message)
        self.assertIn("Not Found", cm.exception.message)


if __name__ == '__main__':
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
