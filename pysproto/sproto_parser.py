from enum import Enum

from pysproto.sproto import Sproto
from pysproto.sproto_interpreter import SprotoInterpreter, SprotoTokenizer


class SourceType(Enum):
    STRING = 0
    FILE = 1


class Sprotoparser:
    __src: str
    __type: SourceType

    def __init__(self, _src: str, _type: SourceType) -> None:
        self.__src = _src
        self.__type = _type

    def parse(self) -> Sproto:
        if self.__type == SourceType.FILE:
            with open(self.__src, 'r') as f:
                return SprotoInterpreter(SprotoTokenizer(f.readlines())).interpret()
        if self.__type == SourceType.STRING:
            return SprotoInterpreter(SprotoTokenizer(self.__src)).interpret()
        return None
