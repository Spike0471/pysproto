from socket import socket
from typing import Tuple, Dict

from pysproto.sproto import Sproto, SprotoProtocol, SprotoType
from pysproto.sproto_encoder import SprotoEncoder


class SprotoClient:
    def __init__(self, ip: str, port: int, client_sproto: Sproto, server_sproto: Sproto) -> None:
        self.__sock: socket = socket()
        self.__client_sproto: Sproto = client_sproto
        self.__server_sproto: Sproto = server_sproto
        self.__session: int = 0
        self.__sessions_protocol: dict[str, SprotoProtocol] = {}
        self.__sock.connect((ip, port))

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.__sock.__exit__(*args)

    def recv_response(self) -> Tuple[int, Dict]:
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
            proto_type = self.__sessions_protocol.get(
                session).get_types('response')
            if proto_type is not None:
                rs, start = SprotoEncoder.decode(
                    proto_type, unpacked[start:unpacked.__len__()])
        return (session, rs)

    def send_reqeust(self, name: str, args: dict = None):
        package = self.__client_sproto.get_package()
        protocol = self.__client_sproto.get_protocol(name)

        header = SprotoEncoder.encode(
            package, {'type': protocol.tag(), 'session': self.__session})
        content = b''
        if args is not None:
            content = SprotoEncoder.encode(protocol.get_types('request'), args)

        packed_data = bytearray(header)
        packed_data.extend(content)
        packed_data = SprotoEncoder.zero_pack(packed_data)
        packed_data = SprotoEncoder.length_pack(packed_data)
        self.__sock.sendall(packed_data)

        self.__sessions_protocol[self.__session] = protocol
        self.__session += 1
