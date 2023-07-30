import csv
import re
from mappings import *
from utils import *
from templates import *


INPUT_PATH = "input/input.tsv"
OUTPUT_PATH = "output/ideologies.txt"


def read_tsv_into_dict(filename):
    result_dict = {}
    special_items_dict = {"Category": {}}

    with open(os.path.join(CWD, filename), "r") as file:
        csv_reader = csv.reader(file, delimiter="\t")
        header = next(csv_reader)  # Get the header row

        next(csv_reader)  # skip second row
        for row in csv_reader:
            inner_dict = {}

            special_items_dict["Category"][row[0]] = row[1]
            for i in range(2, len(header)):
                inner_dict[header[i]] = row[i]

            result_dict[row[0]] = inner_dict

    return result_dict, special_items_dict


def get_ideology_key(idea_name: str):
    if idea_name == "Dictatorship of the Proletariat":
        return "proletariat"
    return idea_name.replace(" ", "_").replace("-", "_").lower()


def split_string(string):
    regex = r"(\+{1,2}|\-{1,2}|0)"
    pattern = re.compile(regex)
    matches = pattern.split(string)
    # Removing empty strings from the resulting list
    matches = [match for match in matches if match]
    return matches


def parse_to_shortcut_and_weight(value):
    pairs = split_string(value.strip())
    if len(pairs) % 2 != 0:
        print("COULDN'T PARSE VALUE")
        return [], []

    return list(zip(pairs[1::2], pairs[0::2]))


ideologies = {}


class Ideology:
    def __init__(self, ideology_name, category):
        self.name = ideology_name
        self.category = category
        self.key = get_ideology_key(ideology_name)
        self.laws = {}

    def parse_law_stances(self, law_group_common_name, law_stances):
        law_group_key = column_name_to_lawgroup[law_group_common_name]
        self.laws[law_group_key] = {}
        for law in law_group_to_law[law_group_key].keys():
            self.laws[law_group_key][law] = "{{PLACEHOLDER}}"
        laws_and_level_lists = parse_to_shortcut_and_weight(law_stances)
        for laws, level in laws_and_level_lists:
            laws_split = [law.strip() for law in laws.split(",")]
            for law in laws_split:
                if law == "":
                    continue
                if not law in law_to_law_groups[law_group_key]:
                    print(f"COULDN'T FIND REVERSE MAP FOR {law_group_key}-{law}")
                    continue
                for law_key in law_to_law_groups[law_group_key][law]:
                    self.laws[law_group_key][law_key] = level_to_word[level.strip()]

    def to_text(self):
        formatted_laws = []
        for law_group_key, laws in self.laws.items():
            laws_approvals = []
            for law_key, approval in laws.items():
                laws_approvals.append(
                    TEMPALTES.ideology_law_approval.format(
                        law_key=law_key, approval_level=approval
                    )
                )
            formatted_laws.append(
                TEMPALTES.ideology_law.format(
                    law_group_key=law_group_key, law_approvals="\n".join(laws_approvals)
                )
            )

        return TEMPALTES.ideology.format(
            laws="".join(formatted_laws), ideology_key=self.key, category=self.category
        )


def main():
    ideology_law_stances, ideology_defines = read_tsv_into_dict(INPUT_PATH)

    for ideology_name, law_group_of_idea in ideology_law_stances.items():
        for law_group_common_name, law_stances in law_group_of_idea.items():
            if law_stances == "":
                continue
            if ideology_name not in ideologies:
                ideologies[ideology_name] = Ideology(
                    ideology_name, ideology_defines["Category"][ideology_name]
                )
            ideology = ideologies[ideology_name]
            ideology.parse_law_stances(law_group_common_name, law_stances)

    save_file_pdx(
        os.path.join(CWD, OUTPUT_PATH),
        "".join([ideology.to_text() for ideology in ideologies.values()]),
    )


if __name__ == "__main__":
    main()
