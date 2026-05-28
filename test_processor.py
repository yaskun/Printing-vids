import unittest
from news_processor import NewsProcessor
import os

class TestNewsProcessor(unittest.TestCase):
    def setUp(self):
        self.processor = NewsProcessor(os.getenv("GEMINI_API_KEY", "dummy"))

    def test_fetch_news_content_invalid_url(self):
        # Probar con una URL que fallará
        result = self.processor.fetch_news_content("http://invalid.url.that.does.not.exist")
        self.assertTrue(result.startswith("Error"))

if __name__ == '__main__':
    unittest.main()
