class SprotoException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)
        self.__args = args

    def print_trace_stack(self) -> None:
        for arg in self.__args:
            print(arg)


class SprotoInterpretException(SprotoException):
    pass


class SprotoEncodeException(SprotoException):
    pass
