import sys,socket,struct

class NetworkIO:
    def __init__(self,s):
        self.sock=s
        
    def data_to_nbyte(self,message):
        if isinstance(message,int):
            if message < (1<<8):
                tag='B'
            elif message < (1<<16):
                tag='H'
            elif message < (1<<32):
                tag='L'
            else:
                tag='Q'
            message=struct.pack('!'+tag,message)
        
            return tag.encode('utf-8')+message
        elif isinstance(message,float):
            tag='d'
            message=struct.pack('!d',message)
        
            return tag.encode('utf-8')+message
        elif isinstance(message,bytes):
            tag='s'
        
            return tag.encode('utf-8')+self.data_to_nbyte(len(message))+message
        elif isinstance(message,str):
            tag='c'
            message=message.encode('utf-8')
        
            return tag.encode('utf-8')+self.data_to_nbyte(len(message))+message
    
    def nbyte_to_data(self):
        size_info={'B':1,'H':2,'L':4,'Q':8,'d':8}
    
        tag=self.sock.recv(1).decode('utf-8')
        if not tag:
            return None
        elif tag in size_info:
            size=size_info[tag]
            number=self.sock.recv(size)
            message=struct.unpack('!'+tag,number)[0]
        elif tag in 'sc':
            size=self.nbyte_to_data()
            if tag=='s':
                message=self.sock.recv(size)
            else:
                bstr=self.sock.recv(size)
                message=bstr.decode('utf-8')
        return message
    
    def write_raw(self,message):
        self.sock.send(message)
    def write(self,message):
        self.sock.send(self.data_to_nbyte(message))
    def read_raw(self,n):
        return self.sock.recv(n)
    def read(self):
        return self.nbyte_to_data()
        
    
def server(host, port):
    listeningSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listeningSock.bind( (host, port) )
    listeningSock.listen()

    sock, sockname = listeningSock.accept()
    handle = NetworkIO(sock)
    while True:
        message = handle.read()
        if not message:
            break
        print('receive',message,'from',sockname)
    sock.close()

    listeningSock.close()

def client(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect( (host, port) )

    handle = NetworkIO(sock)
    handle.write( b'NCNU')
    handle.write( 'Happy Birthday')
    handle.write( 5201314)
    handle.write( 3.1415926535)

    sock.close()

def main():
    if len(sys.argv)!=4:
        print('wrong format')
    else:
        ip=sys.argv[2]
        port=int(sys.argv[3])
        if sys.argv[1]=='server':
            server(ip,port)
        elif sys.argv[1]=='client':
            client(ip,port)
        else:
            print('wrong format')
            
if __name__ == "__main__":
    main()