import logging
from requests.exceptions import RequestException

class BaseFetchDataUseCase:
    MAX_RETRIES = 3

    def __init__(self, api_client):
        self.api_client = api_client

    def execute(self):
        retries = 0
        while retries < self.MAX_RETRIES:
            try:
                response = self.api_client.fetch_data()
                response.raise_for_status()  # Raise an error for bad responses
                return self.process_data(response.json())
            except RequestException as e:
                logging.error(f"Error fetching data: {e}")
                retries += 1
                if retries >= self.MAX_RETRIES:
                    raise self.get_retry_limit_exception()("Max retries reached") from e
                logging.info(f"Retrying... ({retries}/{self.MAX_RETRIES})")
        raise self.get_fetch_error_exception()("Failed to fetch data")

    def process_data(self, data):
        raise NotImplementedError("Subclasses must implement this method")

    def get_fetch_error_exception(self):
        return Exception

    def get_retry_limit_exception(self):
        return Exception
