import os
import unittest
from unittest.mock import patch
from app.utils.llm_provider import LLMProvider

class TestLLMProvider(unittest.TestCase):
    @patch('requests.post')
    def test_generate_text_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "Paris"}]}}
            ]
        }
        response = LLMProvider.generate_text("What is the capital of France?")
        self.assertEqual(response, "Paris")

    @patch('requests.post')
    def test_generate_text_api_error(self, mock_post):
        mock_post.side_effect = Exception("API error")
        response = LLMProvider.generate_text("Test error")
        self.assertIn("[GAP:", response)

if __name__ == "__main__":
    unittest.main()
