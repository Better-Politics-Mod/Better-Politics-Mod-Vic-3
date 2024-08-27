import os
import shutil
from agendas.framework.Agenda import Agenda, EffectRecurrence, Category
from agendas.framework.PdxObject import PdxObject


FOLDER = "support-scripts/agendas/framework-output"
class Generator:
    
    def __init__(self):
        self.scripted_effects = []
        self.on_actions = []
        self.scripted_triggers = []
        self.script_values = []

    def generate(self, categories):
        self.generate_effects(categories)
        self.generate_picker(categories)
        self.write_to_files()

    def generate_picker(self, categories):
        script_values = self.__generate_script_values(categories)
        effect_templates = self.__create_effect_templates(categories)
        scripted_triggers = self.__generate_triggers(self.__get_agendas_from_categories(categories))
        final_scripted_effect = self.__assemble_final_scripted_effect(effect_templates)

        scripted_effects = {
            "bpm_agenda_picker": final_scripted_effect
        }

        self.scripted_effects.append(PdxObject(scripted_effects))
        self.script_values.append(PdxObject(script_values))
        self.scripted_triggers.append(PdxObject(scripted_triggers))

    
    def generate_effects(self, categories):
        self.__generate_effect_for_tick(categories, EffectRecurrence.AGENDA_TICK)
        self.__generate_effect_for_tick(categories, EffectRecurrence.MONTHLY)

    def __get_agendas_from_categories(self, categories):
        return [agenda for category in categories for agenda in category.agendas]
    
    def __generate_triggers(self, agendas: list[Agenda]):
        scripted_triggers = {}
        for agenda in agendas:
            scripted_triggers[agenda.scripted_trigger_name()] = agenda.scripted_trigger()
        return scripted_triggers

    def __generate_script_values(self, categories):
        script_values = {}
        total_weight_list = []

        for category in categories:
            script_values[category.script_value_name()] = category.script_value()
            script_values[category.script_value_name_normalized()] = [
                {"value": 0},
                {"add": category.script_value_name()},
                {"divide": "bpm_agenda_categories_total_weight"},
                {"multiply": 100},
            ]
            total_weight_list.append({"add": category.script_value_name()})

        script_values["bpm_agenda_categories_total_weight"] = [{"value": 0}] + total_weight_list
        
        return script_values

    def __create_effect_templates(self, categories):
        effect_templates = []

        for category in categories:
            effect_templates.append({
                "change_variable": [
                    {"name": "bpm_agenda_category_weight_running_total"},
                    {"add": category.script_value_name_normalized()}
                ]
            })
            effect_templates.append({
                "if": [
                    {
                        "limit": [
                            "var:bpm_agenda_category_random_number <= var:bpm_agenda_category_weight_running_total",
                            {"NOT": {"has_variable": "bpm_agenda_picker_ifelse_ended"}}
                        ]
                    },
                    "# do something here",
                    {"set_variable": "bpm_agenda_picker_ifelse_ended"}
                ]
            })

        return effect_templates

    def __assemble_final_scripted_effect(self, effect_templates):
        final_scripted_effect = [
            {
                "set_variable": [
                    {"name": "bpm_agenda_category_random_number"},
                    {
                        "value": {
                            "integer_range": {
                                "min": 0,
                                "max": 100
                            }
                        }
                    }
                ]
            },
            {
                "set_variable": [
                    {"name": "bpm_agenda_category_weight_running_total"},
                    {"value": 0}
                ]
            }
        ] + effect_templates
        
        return final_scripted_effect

    def __generate_effect_for_tick(self, categories, tick):
        agendas = self.__get_agendas_from_categories(categories)
        scripted_effects = {}
        caller_list = []
        for agenda in agendas:
            if agenda.has_tick_effect(tick):
                scripted_effects[agenda.scripted_effect_name(tick)] = agenda.scripted_effect(tick)
                caller_list.append(
                    {
                        "if": [
                            {
                                "limit": {
                                    "bpm_has_agenda": agenda.id
                                }
                            },
                            {
                                agenda.scripted_effect_name(tick): True
                            }
                        ],
                    }
                )
        raw_on_action = [
            { 
                tick.get_pulse(): {
                    "on_actions": [
                        f"on_bpm_{tick}_tick"
                    ]
                }
            },
            { f"on_bpm_{tick}_tick": caller_list }
        ]

        self.on_actions.append(PdxObject(raw_on_action))
        self.scripted_effects.append(PdxObject(scripted_effects))

    def delete_all_files_in_folder(self, folder_path):
        if os.path.exists(folder_path) and os.path.isdir(folder_path):
            for filename in os.listdir(folder_path):
                file_path = os.path.join(folder_path, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)  
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path) 
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        else:
            print(f"The folder {folder_path} does not exist or is not a directory.")

    def write_to_files(self):
        self.delete_all_files_in_folder(FOLDER)
        for k, v in self.__dict__.items():
            with open(f"{FOLDER}/{k}.txt", "w") as f:
                f.write('\n'.join(str(x) for x in v))
