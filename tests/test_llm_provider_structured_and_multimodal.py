import unittest
from unittest.mock import patch
from app.utils.llm_provider import LLMProvider

class TestLLMProviderStructuredAndMultimodal(unittest.TestCase):
    @patch('requests.post')
    def test_generate_structured_response_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": '{"summary": "Audit logging is essential."}'}]}}
            ]
        }
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
        response = LLMProvider.generate_structured_response("Summarize audit logging", schema)
        self.assertIn("Audit logging is essential", response)

    @patch('requests.post')
    def test_generate_structured_response_api_error(self, mock_post):
        mock_post.side_effect = Exception("API error")
        schema = {"type": "object", "properties": {"summary": {"type": "string"}}}
        response = LLMProvider.generate_structured_response("Summarize audit logging", schema)
        self.assertIn("[GAP:", response)

    @patch('requests.post')
    def test_generate_multimodal_response_success(self, mock_post):
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {
            "candidates": [
                {"content": {"parts": [{"text": "This is an image of a cat."}]}}
            ]
        }
        response = LLMProvider.generate_multimodal_response("Describe this image", "dGVzdGltYWdlZGF0YQ==")
        self.assertIn("cat", response)

    @patch('requests.post')
    def test_generate_multimodal_response_api_error(self, mock_post):
        mock_post.side_effect = Exception("API error")
        response = LLMProvider.generate_multimodal_response("Describe this image", "dGVzdGltYWdlZGF0YQ==")
        self.assertIn("[GAP:", response)

if __name__ == "__main__":
    unittest.main()
