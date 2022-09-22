from pysproto.sproto_client import SprotoClient
from pysproto.sproto_parser import SourceType, Sprotoparser

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

if __name__ == '__main__':
    client_sproto = Sprotoparser(c2s, SourceType.STRING).parse()
    server_sproto = Sprotoparser(s2c, SourceType.STRING).parse()
    with SprotoClient(TARGET_SERVER, TARGET_PORT, client_sproto, server_sproto) as client:
        client.send_reqeust('handshake')
        client.recv_response()
        client.send_reqeust('set', {'what': 'hello', 'value': 'world'})
        client.recv_response()
        client.send_reqeust('get', {'what': 'hello'})
        client.recv_response()
        client.send_reqeust('quit')
        client.recv_response()
