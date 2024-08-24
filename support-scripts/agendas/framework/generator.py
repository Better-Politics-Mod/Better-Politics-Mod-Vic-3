from agendas.framework.Agenda import Agenda, EffectRecurrence, Category
from agendas.framework.PdxObject import PdxObject

# generate effects
# generate picker (the picker will also call the on_add effect if applicable)
# generate script value consts

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

