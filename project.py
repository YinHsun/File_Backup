import socket,threading,os,json,glob

class NetAPI:
    FILE_TAG_SIZE       = 8
    FILE_END_TAG        = b'FILEEND0'
    FILE_NAME_TAG       = b'FILENAME'
    FILE_SIZE_TAG       = b'FILESIZE'
    FILE_CONTENT_TAG    = b'FILEDATA'
    FILE_ABORT_TAG      = b'FILEABRT'
    
    def __init__(self,s):
        from NetworkIO import NetworkIO
        self.Handle=NetworkIO(s)
    
    def send_tag(self,t):
        self.Handle.write_raw(t)
    def send_data(self,d):
        self.Handle.write(d)
    def send_filename(self,n):
        self.send_data(n)
    def send_filesize(self,s):
        self.send_data(s)
    def send_filecontent(self,d):
        self.send_data(d)
        
    def send_file(self,f):
        filename=f
        filesize = os.path.getsize(f)
        self.send_tag(self.FILE_NAME_TAG)
        self.send_filename(filename)
        self.send_tag(self.FILE_SIZE_TAG)
        self.send_filesize(filesize)
        filedata = open(f,'rb').read()
        self.send_tag(self.FILE_CONTENT_TAG)
        self.send_filecontent(filedata)
        self.send_tag(self.FILE_END_TAG)

    def PrintTree(self,d):
        topDir=os.path.dirname(d[0])
        for i in d:
            if i==d[0]:
                print(os.path.basename(i))
                continue
            layer=0
            dirtory=os.path.dirname(i)
            basename=os.path.basename(i)
            while dirtory != topDir:
                layer+=1
                dirtory=os.path.dirname(dirtory)
            for i in range(layer-1):
                print('|   ',end='')
            print('|')
            for i in range(layer-1):
                print('|   ',end='')
            print('+---%s'%(basename))
    def scan_all_file(self,path,Dir):
        if os.path.isdir(path):
            Dir.append(path)
            for filename in glob.glob(path+'/*'):
                self.scan_all_file(filename,Dir)
        else:
            Dir.append(path)
    def scan_dir(self,path,Dir,File):
        if os.path.isdir(path):
            Dir.append(path)
            for filename in glob.glob(path+'/*'):
                self.scan_dir(filename,Dir,File)
        else:
            File.append(path)
    def send_directory(self,d):
        Dir=[]
        File=[]
        self.scan_dir(d,Dir,File)
        self.send_data(json.dumps(Dir))
        self.send_data(json.dumps(File))
        for i in File:
            self.send_file(i)
    def simplify_List(self,File,cut_dir):
        new_list=[]
        for i in File:
            new_list.append(i[cut_dir+1:])
        return new_list
        
    def recv_tag(self):
        return self.Handle.read_raw(self.FILE_TAG_SIZE)
    def recv_data(self):
        return self.Handle.read()
    def recv_file(self,directory):
        result={}
        while True:
            tag=self.recv_tag()
            if not tag or tag in [self.FILE_END_TAG, self.FILE_ABORT_TAG]:
                break
            else:
                data=self.recv_data()
                result[tag]=data
        result[self.FILE_NAME_TAG]=os.path.basename(result[self.FILE_NAME_TAG])
        with open(directory+'\\'+result[self.FILE_NAME_TAG],'wb') as fp:
            fp.write(result[self.FILE_CONTENT_TAG])
    
    def recv_file_with_directory(self,directory,len_Dir):
        result={}
        while True:
            tag=self.recv_tag()
            if not tag or tag in [self.FILE_END_TAG, self.FILE_ABORT_TAG]:
                break
            else:
                data=self.recv_data()
                result[tag]=data
        result[self.FILE_NAME_TAG]=result[self.FILE_NAME_TAG][len_Dir+1:]
        with open(directory+'\\'+result[self.FILE_NAME_TAG],'wb') as fp:
            fp.write(result[self.FILE_CONTENT_TAG])
    def recv_directory(self,directory):
        Dir=json.loads(self.recv_data())
        File=json.loads(self.recv_data())
        cut_dir=os.path.dirname(Dir[0])
        for i in Dir:
            if not os.path.exists(directory+'\\'+i[len(cut_dir)+1:]):
                os.makedirs(directory+'\\'+i[len(cut_dir)+1:])
        for i in range(len(File)):
            self.recv_file_with_directory(directory,len(cut_dir))

def server_thread(sock,sockname,user_info):
    handle=NetAPI(sock)
    while True:
        user_name=handle.recv_data()
        if user_name in user_info:
            handle.send_data('Please enter your password.')
        else:
            handle.send_data('It\'s the first time that you arrive here,please sign up your password.')
        password=handle.recv_data()
        if user_name in user_info and password!=user_info[user_name]:
            handle.send_data('Login failed.')
        else:
            handle.send_data('Login successed.')
            break
    user_dic='D:\\user_file\\'+user_name
    if user_name not in user_info:
        user_info[user_name]=password
        with open('D:\\user_info.json','w') as fp:
            json.dump(user_info,fp)
        os.makedirs(user_dic)
    while True:
        command=handle.recv_data()
        if command=='1':
            message=handle.recv_data()
            if message=='True':
                handle.recv_file(user_dic)
                handle.send_data('File upload successfully.')
        elif command=='2':
            Dir=[]
            handle.scan_all_file(user_dic,Dir)
            handle.send_data(json.dumps(Dir))
        elif command=='3':
            Dir=[]
            File=[]
            handle.scan_dir(user_dic,Dir,File)
            list_file=handle.simplify_List(File,len(user_dic))
            filename=handle.recv_data()
            if filename not in list_file:
                handle.send_data('There is no such a file named \'%s\' ,please press 2 to search it again.'%(filename))
            else:
                handle.send_data('True')
                message=handle.recv_data()
                if message=='True':
                    handle.send_file(user_dic+'\\'+filename)
        elif command=='4':
            message=handle.recv_data()
            if message=='True':
                handle.recv_directory(user_dic)
                handle.send_data('Directory upload successfully.')
        elif command=='5':
            Dir=[]
            File=[]
            handle.scan_dir(user_dic,Dir,File)
            list_directory=handle.simplify_List(Dir,len(user_dic))
            directory=handle.recv_data()
            if directory not in list_directory:
                handle.send_data('There is no such a directory named \'%s\' ,please press 2 to search it again.'%(directory))
            else:
                handle.send_data('True')
                message=handle.recv_data()
                if message=='True':
                    handle.send_directory(user_dic+'\\'+directory)
        elif command=='6':
            Dir=[]
            File=[]
            handle.scan_dir(user_dic,Dir,File)
            list_file=handle.simplify_List(File,len(user_dic))
            filename=handle.recv_data()
            if filename not in list_file:
                handle.send_data('There is no such a file named \'%s\' ,please press 2 to search it again.'%(filename))
            else:
                handle.send_data('True')
                reply=handle.recv_data()
                if reply in ['y','yes','Y','YES']:
                    os.remove(user_dic+'\\'+filename)
                    handle.send_data('Remove successfully.')
                else:
                    handle.send_data('False')
        elif command=='7':
            Dir=[]
            File=[]
            handle.scan_dir(user_dic,Dir,File)
            list_directory=handle.simplify_List(Dir,len(user_dic))
            directory=handle.recv_data()
            if directory not in list_directory:
                handle.send_data('There is no such a directory named \'%s\' ,please press 2 to search it again.'%(directory))
            else:
                handle.send_data('True')
                reply=handle.recv_data()
                if reply in ['y','yes','Y','YES']:
                    import shutil
                    shutil.rmtree(user_dic+'\\'+directory)
                    handle.send_data('Remove successfully.')
                else:
                    handle.send_data('False')
        elif command=='8':
            print(sockname,'is leaving.')
            break
    sock.close()

def server(ip, port):
    listeningSock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    listeningSock.bind( (ip, port) )
    listeningSock.listen(5)

    if not os.path.exists('D:\\user_info.json'):
        with open('D:\\user_info.json','w') as fp:
            json.dump({},fp)
    if not os.path.exists('D:\\user_file'):
        os.makedirs('D:\\user_file')
    with open('D:\\user_info.json','r') as fp:
        user_info=json.load(fp)
    threads=[]
    while True:
        sock,sockname=listeningSock.accept()
        print('Listen from',sockname)
        new_threads=[]
        for thread in threads:
            thread.join(0.1)
            if thread.is_alive():
                new_threads.append(thread)
        threads=new_threads
        thread=threading.Thread(target=server_thread,args=(sock,sockname,user_info))
        thread.start()
        threads.append(thread)

def command_hint():
    for i in range(20):
            if i!=19:
                print('~',end='')
            else:
                print('~')
    print('Please input 1~8')
    print('1.Send file\n2.See file tree\n3.Retrieve file\n4.Send directory\n5.Retrieve directory\n6.Remove file\n7.Remove directory\n8.Quit')
    for i in range(20):
        if i!=19:
            print('~',end='')
        else:
            print('~')
def isfile(f):
    return os.path.isfile(f)
def isdir(d):
    return os.path.isdir(d)
def client(ip, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect( (ip, port) )

    handle = NetAPI(sock)
    while True:
        print('Please input your user name.')
        name=input()
        if name=='..':
            print('Invalid name')
            continue
        handle.send_data(name)
        message=handle.recv_data()
        print(message)
        password=input()
        handle.send_data(password)
        message=handle.recv_data()
        print(message)
        if message == 'Login successed.':
            break
    
    while True:
        command_hint()
        command=input()
        handle.send_data(command)
        if command=='1':
            print('Which file do you want to send?')
            filename=input()
            if isfile(filename):
                handle.send_data('True')
                handle.send_file(filename)
                message=handle.recv_data()
                print(message)
            else:
                print('There is no file named %s in your computer'%(filename))
                handle.send_data('False')
        elif command=='2':
            Dir=json.loads(handle.recv_data())
            handle.PrintTree(Dir)
        elif command=='3':
            print('Which file do you want to retrieve?')
            filename=input()
            handle.send_data(filename)
            message=handle.recv_data()
            if message!='True':
                print(message)
            else:
                print('Where do you want this file to store?')
                retrieve_dic=input()
                if not os.path.exists(retrieve_dic):
                    print('There is no %s file in your computer,please check it again.'%(retrieve_dic))
                    handle.send_data('False')
                else:
                    handle.send_data('True')
                    handle.recv_file(retrieve_dic)
                    print('File retrieve successfully.')
        elif command=='4':
            print('Which directory do you want to send?')
            directory=input()
            if isdir(directory):
                handle.send_data('True')
                handle.send_directory(directory)
                message=handle.recv_data()
                print(message)
            else:
                handle.send_data('False')
                print('There is no %s directory in your computer.'%(directory))
        elif command=='5':
            print('Which directory do you want to retrieve?')
            directory=input()
            handle.send_data(directory)
            message=handle.recv_data()
            if message!='True':
                print(message)
            else:
                print('Where do you want this file to store?')
                retrieve_dic=input()
                if not os.path.exists(retrieve_dic):
                    print('There is no %s in your computer,please check it again.'%(retrieve_dic))
                    handle.send_data('False')
                else:
                    handle.send_data('True')
                    handle.recv_directory(retrieve_dic)
                    print('Directory retrieve successfully.')
        elif command=='6':
            print('Which file do you want to remove?')
            filename=input()
            handle.send_data(filename)
            message=handle.recv_data()
            if message!='True':
                print(message)
            else:
                print('Are you sure you want to remove %s?Input y or yes.'%(filename))
                reply=input()
                handle.send_data(reply)
                message=handle.recv_data()
                if message!='False':
                    print(message)
        elif command=='7':
            print('Which directory do you want to remove?')
            directory=input()
            handle.send_data(directory)
            message=handle.recv_data()
            if message!='True':
                print(message)
            else:
                print('Are you sure you want to remove %s?Input y or yes.'%(directory))
                reply=input()
                handle.send_data(reply)
                message=handle.recv_data()
                if message!='False':
                    print(message)
        elif command=='8':
            break
    sock.close()

def main():
    import sys
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