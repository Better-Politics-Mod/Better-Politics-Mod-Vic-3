from typing import Union

from common.converter import json_to_pdx

class PdxObject:

    def __init__(self, o: Union[list, dict]):
        self.data = o

    def __str__(self):
        return json_to_pdx(self.data)

    