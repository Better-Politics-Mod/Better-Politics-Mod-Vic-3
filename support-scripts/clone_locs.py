import os
import re
from pathlib import Path

english_path = "../better-politics-mod/localization/english"
english_dir = Path(english_path)
languages = [
    "braz_por",
    "french",
    "german",
    "japanese",
    "korean",
    "polish",
    "russian",
    "simp_chinese",
    "spanish",
    "turkish",
]
languages_with_loc = {
    "simp_chinese",
}
loc_dict = {language: {} for language in languages}


def extract_loc_key_text(line: str):
    match = re.match(r'([\w.]+):\d+\s+"(.*?)"(?:\s*#|$)', line.strip())
    if match:
        key, text = match.groups()
        return key, text
    return None, None


def clone_file(file: Path):
    loc_dict_english = {}
    english_lines = []
    with open(file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        english_lines = lines
        for line in lines:
            key, text = extract_loc_key_text(line)
            if key:
                loc_dict_english[key] = text
    for language in languages:
        new_path = str(file).replace("english", language)
        new_path_dir = os.path.dirname(new_path)
        os.makedirs(new_path_dir, exist_ok=True)
        print(f"Processing {new_path}")
        if language in languages_with_loc:
            loc_dict = {}
            if os.path.exists(new_path):
                with open(new_path, "r", encoding="utf-8-sig") as f2:
                    lines = f2.readlines()
                    for line in lines:
                        key, text = extract_loc_key_text(line)
                        if key:
                            loc_dict[key] = text
            with open(new_path, "a", encoding="utf-8-sig") as f2:
                f2.write("\n")
                for key, text in loc_dict_english.items():
                    if key not in loc_dict:
                        f2.write(f' {key}:0 "{loc_dict_english[key]}"\n')
        else:
            with open(new_path, "w", encoding="utf-8-sig") as f2:
                for line in english_lines:
                    if line.startswith("l_english"):
                        f2.write(line.replace("l_english", f"l_{language}"))
                    else:
                        f2.write(line)


def clone_files(dir: Path):
    files = dir.iterdir()
    for file in files:
        if not str(file).endswith(".yml"):
            clone_files(file)
        else:
            clone_file(file)


if __name__ == "__main__":
    clone_files(english_dir)
