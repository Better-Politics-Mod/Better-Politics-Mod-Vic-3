from agendas.framework.Agenda import Agenda, EffectRecurrence, Category
from agendas.framework.PdxObject import PdxObject

# generate effects
# generate picker
# generate script value consts

def generate_effects(categories: list[Category]):
    agendas = [ agenda for category in categories for agenda in category.agendas ]
    # we want to create a scripted effect for each agenda
    # We start with EffectRecurrence.AGENDA_TICK, then EffectRecurrence.MONTHLY, then EffectRecurrence.ON_ADDED
    scripted_effects = {}
    caller_list = []
    for agenda in agendas:
        scripted_effects[agenda.scripted_effect_name(EffectRecurrence.AGENDA_TICK)] = agenda.scripted_effect(EffectRecurrence.AGENDA_TICK)
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
                        agenda.scripted_effect_name(EffectRecurrence.AGENDA_TICK): True
                    }
                ],
            }
        )
    raw_on_action = [
        { 
            "on_yearly_pulse_country": {
                "on_actions": [
                    "on_bpm_agenda_tick"
                ]
            }
        },
        { "on_bpm_agenda_tick": caller_list }
    ]

    print(PdxObject(raw_on_action))
    print(PdxObject(scripted_effects))