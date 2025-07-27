import unittest
from unittest.mock import patch
from app.utils.llm_provider import LLMProvider
import logging

class TestLLMProviderEdgeCases(unittest.TestCase):
    @patch('requests.post')
    def test_generate_text_empty_prompt(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": ""}]}}
            ]
        }
        import asyncio
        response = asyncio.run(LLMProvider.generate_text(""))
        self.assertEqual(response, "")

    @patch('requests.post')
    def test_generate_text_malformed_response(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"unexpected": "structure"}
        import asyncio
        response = asyncio.run(LLMProvider.generate_text("Test malformed"))
        self.assertIn("[GAP:", response)

    @patch('requests.post')
    def test_generate_text_json_decode_error(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.side_effect = Exception("JSON decode error")
        import asyncio
        response = asyncio.run(LLMProvider.generate_text("Test JSON error"))
        self.assertIn("[GAP:", response)

    @patch('requests.post')
    def test_generate_text_logging(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "LogTest"}]}}
            ]
        }
        import asyncio
        with self.assertLogs(level='INFO') as log:
            response = asyncio.run(LLMProvider.generate_text("Log this"))
            self.assertIn("LogTest", response)
            self.assertTrue(any("Calling LLM" in message for message in log.output))

if __name__ == "__main__":
    unittest.main()
