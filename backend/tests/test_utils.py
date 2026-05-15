import unittest

from utils import validate_urls


class ValidateUrlsTests(unittest.TestCase):
    def test_adds_https_protocol_to_valid_domain(self):
        result = validate_urls(['example.com'])

        self.assertTrue(result['valid'])
        self.assertEqual(result['valid_urls'], ['https://example.com'])

    def test_rejects_invalid_urls(self):
        result = validate_urls(['not-a-url'])

        self.assertFalse(result['valid'])
        self.assertEqual(result['message'], 'No valid URLs found')

    def test_limits_maximum_urls_per_request(self):
        urls = [f'https://example{i}.com' for i in range(11)]

        result = validate_urls(urls)

        self.assertFalse(result['valid'])
        self.assertEqual(result['message'], 'Maximum 10 URLs allowed per request')


if __name__ == '__main__':
    unittest.main()
