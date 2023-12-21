import os
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


def clone_file(file: Path, language: str):
    with open(file, "r", encoding="utf-8-sig") as f:
        lines = f.readlines()
        new_path = f.name.replace("english", language)
        new_path_dir = os.path.dirname(new_path)
        os.makedirs(new_path_dir, exist_ok=True)
        print(f"Writing to {new_path}")
        with open(new_path, "w", encoding="utf-8-sig") as f2:
            for line in lines:
                if line.startswith("l_english"):
                    f2.write(line.replace("l_english", f"l_{language}"))
                else:
                    f2.write(line)


def clone_files(dir: Path, language: str):
    files = dir.iterdir()
    for file in files:
        if not str(file).endswith(".yml"):
            clone_files(file, language)
        else:
            clone_file(file, language)


for language in languages:
    print(f"Cloning files to {language}.")
    clone_files(english_dir, language)
