from enum import Enum
from pysproto.sproto_exception import SprotoInterpretException
from pysproto.sproto import Sproto, SprotoField, SprotoProtocol, SprotoType
from typing import Union

import re


class TokenType(Enum):
    UNKOWN = -1
    TYPE_NAME = 0
    ARRAY_NAME = 1
    NORMAL_NAME = 2
    TAG = 3
    SIGN = 4
    EOF = 5


class SprotoToken:
    content: str
    token_type: TokenType

    def __init__(self, t: TokenType, c: str = '') -> None:
        self.content = c
        self.token_type = t


BLANK = [' ', '\n', '\r', '\0', '\t', '\f']

TYPE_NAME_PATTERN = '\.[a-zA-Z]+'
NORMAL_NAME_PATTERN = '[a-zA-Z]+'
ARRAY_NAME_PATTERN = '\*[a-zA-Z]+'
TAG_PATTERN = '\d+'
SIGN_PATTERN = '\{|\}|\:'


class SprotoTokenizer:
    __tokens: list[SprotoToken] = []
    __current_token_index: int = 0
    __patterns = {
        TYPE_NAME_PATTERN: TokenType.TYPE_NAME,
        NORMAL_NAME_PATTERN: TokenType.NORMAL_NAME,
        ARRAY_NAME_PATTERN: TokenType.ARRAY_NAME,
        TAG_PATTERN: TokenType.TAG,
        SIGN_PATTERN: TokenType.SIGN
    }

    def __init__(self, lines: Union[str, list[str]] = None) -> None:
        if lines is not None:
            if type(lines) is str:
                lines = lines.strip()
                self.add_line(lines)
            else:
                self.add_lines(lines)

    def add_line(self, line: str):
        i = 0
        while i < line.__len__():
            while line[i] in BLANK:
                i += 1
            remain = line[i:line.__len__()]
            found = False
            for key in self.__patterns.keys():
                matched = re.match(key, remain)

                if matched is not None:
                    found = True
                    span = matched.span()
                    i += span[1]
                    content = matched.group().strip()
                    self.__tokens.append(SprotoToken(
                        self.__patterns[key], content))
                    break
            if not found:
                raise SprotoInterpretException(
                    'token {}... doesn\'t match any pattern.'.format(remain[0:10]))

    def add_lines(self, lines: list[str]):
        for line in lines:
            line = line.strip()
            self.add_line(line)

    def get_token(self):
        if self.__current_token_index >= self.__tokens.__len__():
            return SprotoToken(TokenType.EOF)
        self.__current_token_index += 1
        return self.__tokens[self.__current_token_index - 1]

    def put_back(self):
        self.__current_token_index -= 1


'''
Rules:
init->[SprotoTyes|SprotoProtocols]->EOF    Sproto
normal_name->tag->':'->type|SprotoType         SprotoField
normal_name|type_name->'{'->[SprotoFields]->'}'  SprotoType
normal_name->tag->'{'->[SprotoTypes]->'}'      SprotoProtocol
'''


def is_end_token(token: SprotoToken):
    return token.token_type == TokenType.SIGN and token.content == '}'


def is_start_token(token: SprotoToken):
    return token.token_type == TokenType.SIGN and token.content == '{'


def check_start_token(token: SprotoToken):
    if not is_start_token(token):
        raise SprotoInterpretException('syntax error, should be a start token')


def check_token_type(token: SprotoToken, token_type: Union[TokenType, tuple[TokenType]]):
    valid = False
    if type(token_type) is TokenType:
        valid = token.token_type == token_type
    else:
        valid = token.token_type in token_type
    if not valid:
        raise SprotoInterpretException(
            'wrong token type {}, stop interpret!'.format(token.token_type))


class SprotoInterpreter:
    __tokenizer: SprotoTokenizer
    __valid_types = {
        'integer': int,
        'string': str,
    }

    def __init__(self, tokenizer: SprotoTokenizer) -> None:
        self.__tokenizer = tokenizer

    def interpret(self) -> Sproto:
        token = self.__tokenizer.get_token()
        token_type = token.token_type
        token_content = token.content
        sproto_types = {}
        sproto_protocols = {}
        while token_type is not TokenType.EOF:
            if token_type == TokenType.ARRAY_NAME:
                pass
            elif token_type == TokenType.NORMAL_NAME:
                # it must be a protocol
                protocol_name = token_content
                token = self.__tokenizer.get_token()
                check_token_type(token, TokenType.TAG)
                tag = int(token.content)
                token = self.__tokenizer.get_token()
                check_start_token(token)
                sproto_protocols[protocol_name] = self.__interpret_protocol(
                    protocol_name, tag)

            elif token_type == TokenType.TYPE_NAME:
                type_name = token_content[1:token_content.__len__()]
                token = self.__tokenizer.get_token()
                check_start_token(token)
                sproto_type = self.__interpret_type(type_name)
                sproto_types[type_name] = sproto_type
                self.__valid_types[type_name] = sproto_type
            elif token_type == TokenType.TAG:
                pass
            elif token_type == TokenType.SIGN:
                pass

            token = self.__tokenizer.get_token()
            token_type = token.token_type
            token_content = token.content
        return Sproto(sproto_types, sproto_protocols)

    def __interpret_type(self, type_name: str) -> SprotoType:
        fields = []
        token = self.__tokenizer.get_token()
        while not is_end_token(token):
            self.__tokenizer.put_back()
            fields.append(self.__interpret_field())
            token = self.__tokenizer.get_token()
        return SprotoType(type_name, fields)

    def __interpret_protocol(self, protocol_name: str, protocol_tag: int) -> SprotoProtocol:
        types = {}

        token = self.__tokenizer.get_token()
        while not is_end_token(token):
            check_token_type(token, TokenType.NORMAL_NAME)
            type_name = token.content
            token = self.__tokenizer.get_token()
            check_start_token(token)
            sproto_type = self.__interpret_type(type_name)
            types[type_name] = sproto_type
            token = self.__tokenizer.get_token()

        return SprotoProtocol(protocol_tag, protocol_name, types)

    def __interpret_field(self) -> SprotoField:
        token = self.__tokenizer.get_token()
        check_token_type(token, TokenType.NORMAL_NAME)
        field_name = token.content

        # must be a tag
        token = self.__tokenizer.get_token()
        check_token_type(token, TokenType.TAG)
        tag = int(token.content)

        # must be a ':'
        token = self.__tokenizer.get_token()
        check_token_type(token, TokenType.SIGN)
        if token.content != ':':
            raise SprotoInterpretException(
                'syntax error {}'.format(token.content))

        # the type, name must in valid types
        token = self.__tokenizer.get_token()
        check_token_type(token, (TokenType.NORMAL_NAME, TokenType.ARRAY_NAME))
        content = token.content
        if token.token_type == TokenType.ARRAY_NAME:
            content = content[1:content.__len__()]
        if content not in self.__valid_types.keys():
            raise SprotoInterpretException(
                'syntax error {}'.format(content))
        if token.token_type == TokenType.NORMAL_NAME:
            field_type = self.__valid_types.get(content)
        elif token.token_type == TokenType.ARRAY_NAME:
            field_type = list[self.__valid_types.get(content)]

        return SprotoField(tag, field_name, field_type)
