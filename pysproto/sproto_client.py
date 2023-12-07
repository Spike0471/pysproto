import socket
from typing import Tuple, Dict

from pysproto.sproto import Sproto, SprotoProtocol, SprotoType
from pysproto.sproto_encoder import SprotoEncoder

import threading


class SprotoClient:
    def __init__(self, ip: str, port: int, client_sproto: Sproto, server_sproto: Sproto) -> None:
        self.__mutex = threading.Lock()
        self.__sock: socket.socket = socket.socket()
        self.__client_sproto: Sproto = client_sproto
        self.__server_sproto: Sproto = server_sproto
        self.__session: int = 0
        self.__sessions_protocol: dict[str, SprotoProtocol] = {}
        self.__sock.connect((ip, port))
        self.__sock.settimeout(0.05)

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.__sock.__exit__(*args)

    def recv_response(self) -> Tuple[int, Dict]:
        session = 0
        rs = None
        with self.__mutex:
            recved = b''
            try:
                recved = self.__sock.recv(1024)
            except socket.timeout:
                return (None, None)
            if recved == b'' or recved == None:
                return (None, None)
            unpacked = SprotoEncoder.zero_unpack(
                SprotoEncoder.length_unpack(recved))
            # it's may be a c2s response or s2c request
            rs, start = SprotoEncoder.decode(
                self.__client_sproto.get_package(), unpacked)
            type = rs.get('type')
            session = rs.get('session')
            if start < unpacked.__len__():
                if type is None:
                    # it's a c2s response
                    proto_type = self.__sessions_protocol.get(
                        session).get_type('response')
                    if proto_type is not None:
                        rsBody, start = SprotoEncoder.decode(
                            proto_type, unpacked[start:unpacked.__len__()])

                        rs = {self.__sessions_protocol.get(
                            session).proto_name(): rsBody}
                else:
                    # it's s2c request
                    protocol = self.__server_sproto.get_protocol_by_tag(type)
                    proto_types = protocol.get_types()
                    rsBody = {}
                    for proto_type in proto_types.values():
                        rsTmp, start = SprotoEncoder.decode(
                            proto_type, unpacked[start:unpacked.__len__()])
                        rsBody.update(rsTmp)
                    rs = {protocol.proto_name(): rsBody}
        return (session, rs)

    def send_reqeust(self, name: str, args: dict = None) -> None:
        with self.__mutex:
            package = self.__client_sproto.get_package()
            protocol = self.__client_sproto.get_protocol(name)

            header = SprotoEncoder.encode(
                package, {'type': protocol.tag(), 'session': self.__session})
            content = b''
            if args is not None:
                content = SprotoEncoder.encode(
                    protocol.get_type('request'), args)

            packed_data = bytearray(header)
            packed_data.extend(content)
            packed_data = SprotoEncoder.zero_pack(packed_data)
            packed_data = SprotoEncoder.length_pack(packed_data)
            self.__sock.sendall(packed_data)

            self.__sessions_protocol[self.__session] = protocol
            self.__session += 1
