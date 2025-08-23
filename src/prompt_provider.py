import yaml


class PromptManager:
    def __init__(self, prompt_file_path: str):
        self.prompt_file_path = prompt_file_path
        self.prompt_cache = {}
        self.load_prompts()

    def load_prompts(self):
        try:
            with open(self.prompt_file_path, "r") as f:
                data = yaml.safe_load(f)
                self.prompt_cache = data.get("prompts", {})
        except FileNotFoundError:
            print(f"Prompt file not found: {self.prompt_file_path}")
            self.prompt_cache = {}

        print("Prompts loaded:", list(self.prompt_cache.keys()))

    def get_prompt(self, key: str) -> str:
        prompt_entry = self.prompt_cache.get(key)
        if prompt_entry:
            return prompt_entry.get("prompt")
        raise KeyError(f"Prompt '{key}' not found in cache.")

    def render_prompt(self, key: str, **kwargs) -> str:
        try:
            raw_prompt = self.get_prompt(key)
            return raw_prompt.format(**kwargs)
        except KeyError as e:
            raise
        except Exception as e:
            raise ValueError(f"Failed to render prompt '{key}': {e}")
