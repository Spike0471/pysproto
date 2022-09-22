from socket import socket

from pysproto.sproto import Sproto, SprotoProtocal, SprotoType
from pysproto.sproto_encoder import SprotoEncoder


class SprotoClient:
    __sock: socket
    __client_sproto: Sproto
    __server_sproto: Sproto
    __session: int
    __sessions_protocal: dict

    def __init__(self, ip: str, port: int, client_sproto: Sproto, server_sproto: Sproto) -> None:
        self.__sock = socket()
        self.__client_sproto = client_sproto
        self.__server_sproto = server_sproto
        self.__session = 0
        self.__sessions_protocal: dict[str, SprotoProtocal] = {}
        self.__sock.connect((ip, port))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.__sock.__exit__(*args)

    def recv_response(self):
        recved = self.__sock.recv(1024)
        if recved == b'':
            return
        unpacked = SprotoEncoder.zero_unpack(
            SprotoEncoder.length_unpack(recved))
        rs, start = SprotoEncoder.decode(
            self.__client_sproto.get_package(), unpacked)
        type = rs.get('type')
        session = rs.get('session')
        if start < unpacked.__len__() and session is not None:
            proto_type = self.__sessions_protocal.get(
                session).get_types('response')
            if proto_type is not None:
                rs, start = SprotoEncoder.decode(
                    proto_type, unpacked[start:unpacked.__len__()])
            print('response :{}'.format(session))
            print('content: {}'.format(rs))

    def send_reqeust(self, name: str, args: dict = None):
        package = self.__client_sproto.get_package()
        protocal = self.__client_sproto.get_protocal(name)

        header = SprotoEncoder.encode(
            package, {'type': protocal.tag(), 'session': self.__session})
        content = b''
        if args is not None:
            content = SprotoEncoder.encode(protocal.get_types('request'), args)

        packed_data = bytearray(header)
        packed_data.extend(content)
        packed_data = SprotoEncoder.zero_pack(packed_data)
        packed_data = SprotoEncoder.length_pack(packed_data)
        self.__sock.sendall(packed_data)

        self.__sessions_protocal[self.__session] = protocal
        self.__session += 1
