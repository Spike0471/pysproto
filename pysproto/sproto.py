from typing import List, Dict


class SprotoField:
    def __init__(self, _tag: int, _name: str, _type: type) -> None:
        self.__tag: int = _tag
        self.__name: str = _name
        self.__type: type = _type

    def tag(self) -> int:
        return self.__tag

    def type_name(self) -> str:
        return self.__name

    def type(self) -> type:
        return self.__type


class SprotoType:
    def __init__(self, _name, _members: List[SprotoField]) -> None:
        self.__name: str = _name
        self.__members: List[SprotoField] = []
        # ensure it's an ascending sequence
        for field in _members:
            current_len = self.__members.__len__()
            insert_i = current_len
            for i in range(0, current_len):
                if self.__members[i].tag() > field.tag():
                    insert_i = i
                    break
            if insert_i == current_len:
                self.__members.append(field)
            else:
                self.__members.insert(insert_i, field)

    def members(self) -> List[SprotoField]:
        return self.__members

    def member(self, tag) -> SprotoField:
        for m in self.__members:
            if m.tag() == tag:
                return m
        return None

    def type_name(self):
        return self.__name


class SprotoProtocol:
    def __init__(self, _tag: int, _name: str, _types: Dict[str, SprotoType] = None) -> None:
        self.__tag: int = _tag
        self.__name: str = _name
        self.__types: Dict[str, SprotoType] = _types

    def tag(self) -> int:
        return self.__tag

    def proto_name(self) -> str:
        return self.__name

    def get_types(self, type_name: str) -> SprotoType:
        if self.__types is None:
            return None
        return self.__types.get(type_name)


class Sproto:
    def __init__(self, _types: Dict[str, SprotoType], _protocols: Dict[str, SprotoProtocol]) -> None:
        self.__types: Dict[str, SprotoType] = _types
        self.__protocols: Dict[str, SprotoProtocol] = _protocols

    def get_package(self) -> SprotoType:
        return self.__types.get('package')

    def get_protocol(self, name: str) -> SprotoProtocol:
        return self.__protocols.get(name)

    def get_type(self, name: str) -> SprotoType:
        return self.__types.get(name)
