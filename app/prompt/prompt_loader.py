"""
    加载提示词文件文本
"""
from pathlib import Path


def load_prompt_file(file_name: str) -> str:
    prompt_path = Path(__file__).parents[2] / "prompt" / f"{file_name}.prompt"
    return prompt_path.read_text(encoding="utf-8")

if __name__ == "__main__":
    print(load_prompt_file("extend_keywords_for_column_recall"))