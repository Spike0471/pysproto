

class SprotoField:
    __tag: int
    __name: str
    __type: type

    def __init__(self, _tag: int, _name: str, _type: type) -> None:
        self.__tag = _tag
        self.__name = _name
        self.__type = _type

    def tag(self) -> int:
        return self.__tag

    def type_name(self) -> str:
        return self.__name

    def type(self) -> type:
        return self.__type


class SprotoType:
    __name: str
    __members: list[SprotoField]

    def __init__(self, _name, _members: list[SprotoField]) -> None:
        self.__name = _name
        self.__members = []
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

    def members(self) -> list[SprotoField]:
        return self.__members

    def member(self, tag) -> SprotoField:
        for m in self.__members:
            if m.tag() == tag:
                return m
        return None

    def type_name(self):
        return self.__name


class SprotoProtocol:
    __tag: int
    __name: str
    __types: dict[str, SprotoType]

    def __init__(self, _tag: int, _name: str, _types: dict[str, SprotoType] = None) -> None:
        self.__tag = _tag
        self.__name = _name
        self.__types = _types

    def tag(self) -> int:
        return self.__tag

    def proto_name(self) -> str:
        return self.__name

    def get_types(self, type_name: str) -> SprotoType:
        if self.__types is None:
            return None
        return self.__types.get(type_name)


class Sproto:
    __types: dict[str, SprotoType]
    __protocols: dict[str, SprotoProtocol]

    def __init__(self, _types: dict[str, SprotoType], _protocols: dict[str, SprotoProtocol]) -> None:
        self.__types = _types
        self.__protocols = _protocols

    def get_package(self) -> SprotoType:
        return self.__types.get('package')

    def get_protocol(self, name: str) -> SprotoProtocol:
        return self.__protocols.get(name)

    def get_type(self, name: str) -> SprotoType:
        return self.__types.get(name)
