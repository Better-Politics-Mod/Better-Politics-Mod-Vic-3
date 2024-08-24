import enum
from typing import Union
from agendas.framework.PdxObject import PdxObject

class EffectRecurrence(enum.Enum):
    AGENDA_TICK = 0
    MONTHLY = 1
    ON_ADDED = 2

    def __str__(self):
        if self == EffectRecurrence.AGENDA_TICK:
            return "agenda_tick"
        elif self == EffectRecurrence.MONTHLY:
            return "monthly"
        elif self == EffectRecurrence.ON_ADDED:
            return "on_added"


class Agenda:
    effects: dict[EffectRecurrence, Union[list, dict]]
    trigger: PdxObject
    weight: int
    name: str

    def __init__(self, name, base_weight):
        self.raw_name = name
        self._name = name.replace("bpm_iga_", "")
        self.effects = {}
        self.weight = base_weight

    def add_effect(self, effect: PdxObject, recurrence: EffectRecurrence):
        self.effects[recurrence] = effect
    
    def set_trigger(self, trigger: PdxObject):
        self.trigger = trigger

    def scripted_effect(self, recurrence: EffectRecurrence):
        #print(self.effects)
        return self.effects[recurrence]
    
    def scripted_effect_name(self, recurrence: EffectRecurrence):
        return f"bpm_iga_{self.name}_{recurrence}_effect"
    
    @property 
    def id(self):
        return f"bpm_agenda_{self.name}_id"

    @property
    def name(self):
        return self._name


class Category:
    def __init__(self, name: str, agendas: list[Agenda]):
        self.name = name
        self.agendas = agendas