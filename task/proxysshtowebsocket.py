from channels.generic.websocket import AsyncWebsocketConsumer

import json
import asyncio
import asyncssh
class MySSHClientSession(asyncssh.SSHClientSession):
    async def init(self,host,socket,inicmd):
        self.host=host
        self.websock=socket
        self.inicmd=inicmd

        self.filterflag=0
        await self.websock.send(text_data=json.dumps({
            'action': 'connectsuccess', 'host': self.host['name']
        }))


    def __del__(self):
        print('i am closing')
    def data_received(self, data, datatype):

        print('self.inicmd',self.inicmd)
        print('type',type(data),type(self.inicmd))
        if self.filterflag==0 and self.inicmd.strip()==data.strip():

            self.filterflag=1
            pass
        else:
            try:
                self.websock.syncsend(json.dumps({
                    'action': 'msg', 'host': self.host['name'],'msg':data
                }))
            except Exception as e:
                print(e)
    def connection_made(self, chan):
        self.chan=chan
        pass
    def connection_lost(self, exc):
        try:
            self.websock.syncsend(json.dumps({
                'action': 'connectfail', 'host': self.host['name']
            }))
        except Exception as e:
            print(e)
        pass

        try:

            self.websock.reopen()
        except Exception as e:
            print(e)

class AsyncConsumer(AsyncWebsocketConsumer):
    sshs={}
    async def connect(self):  # 连接时触发
        print('connected')
        await self.accept()
    def syncsend(self,msg):
        asyncio.create_task(self.send(text_data=msg))
    async def disconnect(self, close_code):  # 断开时触发
        pass
        print('closed')
    def reopen(self):
        asyncio.create_task(self.openssh())
    async def openssh(self,inicmd):
        host=self.host
        try:
            async with asyncssh.connect(host['ip'], port=host['port'], username=host['username'], password=host['password'], known_hosts=None,keepalive_interval=3) as conn:
                chan,session = await conn.create_session(MySSHClientSession,term_type='xterm-color',term_size=(1200, 600))
                await session.init(host, self,inicmd+'\n')
                sftp=await conn.start_sftp_client()

                chan.write(inicmd+'\n')
                self.sshs[host['name']] = [chan, sftp]
                await self.readdir(host['name'])
                await chan.wait_closed()
        except Exception as e:
            print(49,e);
            await self.send(text_data=json.dumps({
                'action': 'connectfail', 'host': self.host['name']
            }))
    async def readdir(self,host,path='.'):

        try:
            print('why??path',path)
            print(host)
            tmp=await self.sshs[host][1].stat(path)
            print('tmpreuslt:',tmp)
            dirs=await self.sshs[host][1].readdir(path)
            print(dirs)
            files=[{'filename':f.filename,'isdir':f.longname[0]=='d'} for f in dirs if f.filename!='.']
            files=sorted(files,key=lambda item:(-item['isdir'],item['filename']))
            print(files)
            await self.send(text_data=json.dumps({
                    'action': 'files','host':host,'data':files,'currentpath':path
                }))
        except Exception as e:
            print(67,e)
    async def readfile(self,host,filename):

        try:
            file=await self.sshs[host][1].open(filename)
            data=await file.read()
            await file.close()

            await self.send(text_data=json.dumps({
                    'action': 'filedata','host':host,'data':data,'filename':filename
                }))
        except Exception as e:
            print(81,e)

    async def receive(self, text_data=None, bytes_data=None):  # 接收消息时触发
        text_data_json = json.loads(text_data)
        print(text_data_json)
        action = text_data_json['action']
        if action=='connect':
            await self.send(text_data=json.dumps({
                'action': 'replyconnect'
            }))
        elif action=='openterminal':
            host=text_data_json['host']
            self.host=host
            inicmd=text_data_json['inicmd']
            print(inicmd)
            asyncio.create_task(self.openssh(inicmd))
        elif action=='msg':
            host=text_data_json['host']
            msg=text_data_json['msg']
            self.sshs[host][0].write(msg)
        elif action=='readdir':
            host = text_data_json['host']
            path=text_data_json['path']
            asyncio.create_task(self.readdir(host,path))
        elif action=='readfile':
            host = text_data_json['host']
            path=text_data_json['path']
            asyncio.create_task(self.readfile(host,path))







    # Receive message from room group
    async def system_message(self, event):
        print(event)
        message = event['message']

        # Send message to WebSocket单发消息
        await self.send(text_data=json.dumps({
            'message': message
        }))