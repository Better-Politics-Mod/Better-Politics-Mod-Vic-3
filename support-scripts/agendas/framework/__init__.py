from agendas.framework.Agenda import Agenda, EffectRecurrence, Category
from agendas.framework.generator import Generator

def main():
    institutional_exploitation = Agenda("institutional_exploitation", 0)
    ideological_grifting = Agenda("ideological_grifting", 1)
    institutional_exploitation.add_effect(["# Do stuff every agenda tick"], EffectRecurrence.AGENDA_TICK)
    institutional_exploitation.set_trigger({"always": True})
    ideological_grifting.add_effect(["# Do stuff every agenda tick"], EffectRecurrence.AGENDA_TICK)
    ideological_grifting.add_effect(["# Do stuff on agenda activation"], EffectRecurrence.ON_ADDED)
    ideological_grifting.set_trigger({"always": True})
    exploitation = Category("exploitation", [institutional_exploitation, ideological_grifting])

    obj = Generator()
    obj.generate([exploitation])
