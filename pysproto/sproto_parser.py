from enum import Enum

from pysproto.sproto import Sproto
from pysproto.sproto_interpreter import SprotoInterpreter, SprotoTokenizer


class SourceType(Enum):
    STRING = 0
    FILE = 1


class Sprotoparser:
    def __init__(self, _src: str, _type: SourceType) -> None:
        self.__src: str = _src
        self.__type: SourceType = _type

    def parse(self) -> Sproto:
        if self.__type == SourceType.FILE:
            with open(self.__src, 'r') as f:
                return SprotoInterpreter(SprotoTokenizer(f.readlines())).interpret()
        if self.__type == SourceType.STRING:
            return SprotoInterpreter(SprotoTokenizer(self.__src)).interpret()
        return None
