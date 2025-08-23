import json
from typing import List

def extract_original_prompts(input_file: str, output_file: str) -> None:
    """
    Reads a JSON dataset, extracts all original_fact.prompts,
    and writes them to a new JSON file as a list of strings.
    """
    # Load the input JSON
    with open(input_file, "r", encoding="utf-8") as f:
        data = json.load(f)

    prompts: List[str] = []

    # Traverse dataset entries safely
    for item in data:
        original_fact = item.get("edit", {}).get("original_fact", {})
        prompt = original_fact.get("prompt")
        if prompt:
            prompts.append(prompt)

    # Write just the list of strings
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

    print(f"✅ Extracted {len(prompts)} prompts to {output_file}")
if __name__ == "__main__":
    # Example usage
    extract_original_prompts("./data/benchmark/popular.json", "./data/benchmark/popular_prompts.json")
    extract_original_prompts("./data/benchmark/random.json", "./data/benchmark/random_prompts.json")