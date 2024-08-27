from agendas.framework.Agenda import Agenda, EffectRecurrence, Category
from agendas.framework.PdxObject import PdxObject
from agendas.framework.generator import PdxObjectList

def main():
    institutional_exploitation = Agenda("institutional_exploitation", 0)
    ideological_grifting = Agenda("ideological_grifting", 1)
    institutional_exploitation.add_effect({"set_country_flag": "bpm_institutional_exploitation"}, EffectRecurrence.AGENDA_TICK)
    ideological_grifting.add_effect({"set_country_flag": "bpm_ideological_grifting"}, EffectRecurrence.AGENDA_TICK)
    exploitation = Category("exploitation", [institutional_exploitation, ideological_grifting])

    obj = PdxObjectList()
    obj.generate_effects([exploitation])
    print(obj.script_values)