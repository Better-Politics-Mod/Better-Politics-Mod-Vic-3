import enum
from typing import Union

class EffectRecurrence(enum.Enum):
    AGENDA_TICK = 0
    MONTHLY = 1
    ON_ADDED = 2

    def __str__(self):
        if self == EffectRecurrence.AGENDA_TICK:
            return "agenda"
        elif self == EffectRecurrence.MONTHLY:
            return "monthly"
        elif self == EffectRecurrence.ON_ADDED:
            return "on_added"
        
    def get_pulse(self):
        if self == EffectRecurrence.AGENDA_TICK:
            return "on_yearly_pulse_country"
        elif self == EffectRecurrence.MONTHLY:
            return "on_monthly_pulse_country"


class Agenda:
    effects: dict[EffectRecurrence, Union[list, dict]]
    trigger: Union[list, dict]
    name: str
    _id: int

    def __init__(self, name, id):
        self.raw_name = name
        self._name = name.replace("bpm_iga_", "")
        self.effects = {}
        self._id = id

    def add_effect(self, effect: Union[list, dict], recurrence: EffectRecurrence):
        self.effects[recurrence] = effect
    
    def set_trigger(self, trigger: Union[list, dict]):
        self.trigger = trigger

    def scripted_trigger(self):
        return self.trigger
    
    def scripted_trigger_name(self):
        return f"bpm_iga_{self.name}_possible_trigger"

    def scripted_effect(self, recurrence: EffectRecurrence):
        #print(self.effects)
        return self.effects[recurrence]
    
    def has_tick_effect(self, recurrence: EffectRecurrence):
        return recurrence in self.effects
    
    def scripted_effect_name(self, recurrence: EffectRecurrence):
        return f"bpm_iga_{self.name}_{recurrence}_effect"
    
    @property 
    def id(self):
        return f"bpm_agenda_{self.name}_id"

    @property
    def name(self):
        return self._name


class Category:
    def __init__(self, name: str, agendas: list[Agenda], weight: Union[list, dict]={'value': 100}):
        self.name = name
        self.agendas = agendas
        self.weight = weight

    def script_value_name(self):
        return f"bpm_agenda_{self.name}_category_weight"
    
    def script_value_name_normalized(self):
        return f"bpm_agenda_{self.name}_category_weight_normalized"
    
    def script_value(self):
        return self.weight