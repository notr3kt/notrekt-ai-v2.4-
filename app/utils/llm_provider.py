"""
llm_provider.py - Abstracts LLM API calls to support multiple vendors and open-source models.
SOP-ARC-003
"""
class LLMProvider:
    def __init__(self, provider_name, config):
        self.provider_name = provider_name
        self.config = config

    def generate(self, prompt):
        # [GAP: Route to correct LLM API or local model]
        return "[GAP: LLM output not implemented]"
