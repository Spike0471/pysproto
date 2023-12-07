from pysproto.sproto_client import SprotoClient
from pysproto.sproto_parser import SourceType, Sprotoparser

import threading

TARGET_SERVER = '192.168.2.200'
TARGET_PORT = 8888


c2s = '''
.package {
	type 0 : integer
	session 1 : integer
}

handshake 1 {
	response {
		msg 0  : string
	}
}

get 2 {
	request {
		what 0 : string
	}
	response {
		result 0 : string
	}
}

set 3 {
	request {
		what 0 : string
		value 1 : string
	}
}

quit 4 {}

'''

s2c = '''
.package {
	type 0 : integer
	session 1 : integer
}

heartbeat 1 {}
'''


def recv(client: SprotoClient):
    while True:
        session, res = client.recv_response()
        if res is None:
            continue
        if res.keys().__contains__('handshake'):
            print(res.get('handshake').get('msg'))
        if res.keys().__contains__('heartbeat'):
            print('got heartbeat from server')


if __name__ == '__main__':
    client_sproto = Sprotoparser(c2s, SourceType.STRING).parse()
    server_sproto = Sprotoparser(s2c, SourceType.STRING).parse()
    with SprotoClient(TARGET_SERVER, TARGET_PORT, client_sproto, server_sproto) as client:
        thread = threading.Thread(target=recv, args=(client,))
        thread.daemon = True
        thread.start()
        client.send_reqeust('handshake')
        while True:
            cmd = input()
            if cmd == 'quit':
                client.send_reqeust('quit')
                break
