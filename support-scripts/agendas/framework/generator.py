import os
import shutil
from typing import List, Dict
from agendas.framework.Agenda import Agenda, EffectRecurrence, Category
from common.PdxObject import PdxObject
from common.PdxUtils import PdxUtil

FOLDER: str = "support-scripts/agendas/framework-output"

class Generator:
    
    def __init__(self):
        self.scripted_effects: List[PdxObject] = []
        self.on_actions: List[PdxObject] = []
        self.scripted_triggers: List[PdxObject] = []
        self.script_values: List[PdxObject] = []

    def generate(self, categories: List[Category]) -> None:
        self.generate_effects(categories)
        self.generate_picker(categories)
        self.write_to_files()

    def generate_picker(self, categories: List[Category]) -> None:
        script_values = self.__generate_script_values(categories)
        effect_templates = self.__create_effect_templates(categories)
        scripted_triggers = self.__generate_triggers(self.__get_agendas_from_categories(categories))
        final_scripted_effect = self.__assemble_final_scripted_effect(effect_templates)
        agenda_weights = self.__generate_agenda_weights(categories)

        scripted_effects = PdxUtil.pair("bpm_agenda_picker", final_scripted_effect)

        self.scripted_effects.append(PdxObject(scripted_effects))
        self.script_values.append(PdxObject(script_values))
        self.script_values.append(PdxObject(agenda_weights))
        self.scripted_triggers.append(PdxObject(scripted_triggers))

    def generate_effects(self, categories: List[Category]) -> None:
        self.__generate_effect_for_tick(categories, EffectRecurrence.AGENDA_TICK)
        self.__generate_effect_for_tick(categories, EffectRecurrence.MONTHLY)

    def __get_agendas_from_categories(self, categories: List[Category]) -> List[Agenda]:
        return [agenda for category in categories for agenda in category.agendas]

    def __generate_agenda_weights(self, categories: List[Category]) -> Dict[str, int]:
        agenda_weights = []
        total_weights = []
        normalized_weights = []
        for category in categories:
            v = sum([agenda.weight for agenda in category.agendas])
            total_weight = {
                category.agendas_weight_total_name(): v
            }
            agenda_weight = PdxUtil.pairs(*[(agenda.get_weight_name(), agenda.weight) for agenda in category.agendas])
            normalized_weight = PdxUtil.pairs(*[(agenda.get_weight_name_normalized(), PdxUtil.pairs(("value", agenda.weight), ("divide", v))) for agenda in category.agendas])
            agenda_weights.append(agenda_weight)
            normalized_weights.append(normalized_weight)
            total_weights.append(total_weight)

        return agenda_weights + total_weights + normalized_weights
        
    def __generate_triggers(self, agendas: List[Agenda]) -> Dict[str, str]:
        scripted_triggers: Dict[str, str] = {}
        for agenda in agendas:
            scripted_triggers[agenda.scripted_trigger_name()] = agenda.scripted_trigger()
        return scripted_triggers

    def __generate_script_values(self, categories: List[Category]) -> Dict[str, PdxObject]:
        script_values: Dict[str, PdxObject] = {}
        total_weight_list: List[PdxObject] = []

        for category in categories:
            script_values[category.script_value_name()] = category.script_value()
            script_values[category.script_value_name_normalized()] = PdxUtil.pairs(
                ("value", 0),
                ("add", category.script_value_name()),
                ("divide", "bpm_agenda_categories_total_weight"),
                ("multiply", 100)
            )
            total_weight_list.append(PdxUtil.pair("add", category.script_value_name()))

        script_values["bpm_agenda_categories_total_weight"] = [PdxUtil.pair("value", 0)] + total_weight_list
        
        return script_values

    def __create_effect_templates(self, categories: List[Category]) -> List[PdxObject]:
        effect_templates: List[PdxObject] = []

        for category in categories:
            effect_templates.append(PdxUtil.change_variable("bpm_agenda_category_weight_running_total", category.script_value_name_normalized()))
            effect_templates.append(PdxUtil.if_statement(
                [
                    "var:bpm_agenda_category_random_number <= var:bpm_agenda_category_weight_running_total",
                    PdxUtil.not_condition(PdxUtil.has_variable("bpm_agenda_picker_ifelse_ended"))
                ],
                "# do something here",
                PdxUtil.set_variable("bpm_agenda_picker_ifelse_ended"),
            ))

        return effect_templates

    def __assemble_final_scripted_effect(self, effect_templates: List[PdxObject]) -> List[PdxObject]:
        final_scripted_effect: List[PdxObject] = [
            PdxUtil.set_variable(
                "bpm_agenda_category_random_number",
                PdxUtil.integer_range(0, 100)
            ),
            PdxUtil.set_variable("bpm_agenda_category_weight_running_total", 0)
        ] + effect_templates
        
        return final_scripted_effect

    def __generate_effect_for_tick(self, categories: List[Category], tick: EffectRecurrence) -> None:
        agendas = self.__get_agendas_from_categories(categories)
        scripted_effects: Dict[str, str] = {}
        caller_list: List[PdxObject] = []
        for agenda in agendas:
            if agenda.has_tick_effect(tick):
                scripted_effects[agenda.scripted_effect_name(tick)] = agenda.scripted_effect(tick)
                caller_list.append(PdxUtil.if_statement(
                    *PdxUtil.pairs(
                        ("bpm_has_agenda", agenda.id),
                        (agenda.scripted_effect_name(tick), True)
                    )
                ))

        tick_name = f"on_bpm_{tick}_tick"
                
        raw_on_action = PdxUtil.pairs(
            (tick.get_pulse(), PdxUtil.set_list("on_actions", tick_name)),
            (tick_name, caller_list)
        )

        self.on_actions.append(PdxObject(raw_on_action))
        self.scripted_effects.append(PdxObject(scripted_effects))

    def delete_all_files_in_folder(self, folder_path: str) -> None:
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

    def write_to_files(self) -> None:
        self.delete_all_files_in_folder(FOLDER)
        for k, v in self.__dict__.items():
            with open(f"{FOLDER}/{k}.txt", "w") as f:
                f.write('\n'.join(str(x) for x in v))
