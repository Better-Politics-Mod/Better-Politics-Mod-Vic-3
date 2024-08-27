from agendas.framework.Agenda import Agenda, EffectRecurrence, Category
from agendas.framework.PdxObject import PdxObject

# generate effects
# generate picker (the picker will also call the on_add effect if applicable)
# generate script value consts

# The picker needs to generate a script value for each category
# Then it generates the scripted effect
def generate_picker(categories: list[Category]):
    script_values = {}
    scripted_effects = {}

    total_weight_list = []

    effect_temp = []
    for category in categories:
        script_values[category.script_value_name()] = category.script_value()
        script_values[category.script_value_name_normalized()] = [
            {"value": 0},
            {"add": category.script_value_name()},
            {"divide": "bpm_agenda_categories_total_weight"},
            {"multiply": 100},
        ]
        total_weight_list.append({"add": category.script_value_name()})
        effect_temp.append({
            "change_variable": [
                { "name": "bpm_agenda_category_weight_running_total" },
                {
                    "add": category.script_value_name_normalized()
                }
            ]
        })
        effect_temp.append(
            {
                "if": [
                    {
                        "limit": [
                            "var:bpm_agenda_category_random_number <= var:bpm_agenda_category_weight_running_total",
                            { "NOT": {
                                "has_variable": "bpm_agenda_picker_ifelse_ended"
                            } }
                        ]
                        
                    },
                    "# do something here",
                    { "set_variable": "bpm_agenda_picker_ifelse_ended" }
                ]
            }
        )

    script_values["bpm_agenda_categories_total_weight"] = [{"value": 0}] + total_weight_list


    final_scripted_effect = [ 
        {
            "set_variable": [
                { "name": "bpm_agenda_category_random_number" },
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
                { "name": "bpm_agenda_category_weight_running_total" },
                {
                    "value": 0
                }
            ]
        }
    ] + effect_temp

    scripted_effects["bpm_agenda_picker"] = final_scripted_effect

    return {
        "scripted_effects": [PdxObject(scripted_effects)],
        "script_values": [PdxObject(script_values)]
    }
    

def generate_effects(categories: list[Category]):
    a = generate_effect_for_tick(categories, EffectRecurrence.AGENDA_TICK)
    b = generate_effect_for_tick(categories, EffectRecurrence.MONTHLY)
    return {
        "scripted_effects": [a[1], b[1]],
        "on_actions": [a[0], b[0]]
    }

def generate_effect_for_tick(categories: list[Category], tick: EffectRecurrence):
    agendas = [ agenda for category in categories for agenda in category.agendas ]
    scripted_effects = {}
    caller_list = []
    for agenda in agendas:
        if agenda.has_tick_effect(tick):
            scripted_effects[agenda.scripted_effect_name(tick)] = agenda.scripted_effect(tick)
            #print(agenda.scripted_effect(EffectRecurrence.AGENDA_TICK))
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

    return ( PdxObject(raw_on_action), PdxObject(scripted_effects) ) 



class PdxObjectList:

    def __init__(self):
        self.scripted_effects = []
        self.on_actions = []
        self.scripted_triggers = []
        self.script_values = []

    def __generate(self, f, categories):
        for k, v in f(categories).items():
            setattr(self, k, v)

    def write_to_files(self):
        for k, v in self.__dict__.items():
            with open(f"support-scripts/agendas/framework-output/{k}.txt", "w") as f:
                f.write('\n\n'.join(str(x) for x in v))

    def generate_effects(self, categories):
        self.__generate(generate_effects, categories)
    
    def generate_picker(self, categories):
        self.__generate(generate_picker, categories)
