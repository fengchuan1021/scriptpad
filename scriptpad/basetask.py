import os,sys,json,asyncssh
import django
from pathlib import Path
from asgiref.sync import sync_to_async
if __name__ == '__main__':
    BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent)
    sys.path.append(BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'fengchuan.settings'
os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
django.setup()
import  asyncio,aioredis,aiomysql
from scriptpad.models import TaskHistory,Vp
import datetime
import time
import psutil
from scriptpad.redis import Redis
from scriptpad.db import  Db
import json,aiohttp
class BaseTask:
    dbconfig={'sourcetable':'','databaseip':'','databaseuser':'','databasepasssword':'','databaseport':'','condition':'','conditionarr':[]}
    servers=['']
    name=''
    targetable=''
    args={}
    inputcolums={}
    outputcolums={}
    cron={'enabled':False,'expression':'0 0 * * *'}
    historymodel=None
    progress=0
    updateprogresstask=None
    sendtaskendflag=0
    sleeptime=0
    maxsleeptime=600
    tasklist=''
    resultlist=''
    haschildren=0
    filename=''
    atmobiles = []
    atmobilesoption={'刘金周':'17719959586','刘亚伟':'15542335592'}
    mark=''
    @classmethod
    def setfilename(cls,filename):
        cls.filename=filename
        return cls

    def __init__(self):

        try:
            if len(sys.argv)>=2:
                arg = sys.argv[1]
                
                self.rawarg = json.loads(arg)
                
                
                if self.rawarg['taskid']:
                    
                    try:
                        self.historymodel = TaskHistory.objects.get(id=self.rawarg['taskid'])
                        if self.historymodel.sourcetable:
                            self.historymodel = TaskHistory(name=self.name)
                            self.historymodel.save()
                            self.rawarg['taskid']=self.historymodel.id
                            
                    except Exception as e:
                        print(e)
                        self.historymodel = TaskHistory()

                self.args=self.rawarg['args']

                #if you want change the outtable name ,do it in your own script.

                #if self.rawarg['cron']['enabled']==True:
                #    for key in self.args:
                #        if 'formator' in  self.args[key]:
                #            self.args[key]['value']=self.args[key]['formator'].replace('{now}',datetime.datetime.now().strftime("%Y_%m_%d"))
                try:
                    self.inputcolums=self.rawarg['inputcolums']
                    self.servers=self.rawarg['servers']
                    self.outputcolums={key:self.rawarg['outputcolums'][key] for key in self.outputcolums.keys() & self.rawarg['outputcolums'].keys()}
                    self.dbconfig=self.rawarg['dbconfig']
                    self.tasklist=self.dbconfig['sourcetable']+str(self.dbconfig['databaseport'])+self.dbconfig['databaseuser']+str(time.time())
                    self.historymodel.listname = self.tasklist
                    self.historymodel.sourcetable =self.dbconfig['sourcetable']
                    self.historymodel.name=self.name
                    self.resultlist=self.tasklist+'_result'
                    self.atmobiles=self.rawarg['atmobiles']
                    self.historymodel.save()
                    self.historymodel.outtable = self.args['outtable']['value']
                except Exception as e:
                    pass

            else:
                self.rawarg = {}
        except Exception as e:
            print(53,e)
            self.rawarg = {}
        if self.rawarg:
            self.loop=asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            self.redis=self.loop.run_until_complete(Redis())
            self.db=self.loop.run_until_complete(Db(self.rawarg['dbconfig']))
            self.loop.run_until_complete(self.checkcolum())
            self.updateprogresstask=self.loop.create_task(self.timerupdateprogress())
    async def checkcolum(self):
        if self.outputcolums and self.haschildren==0:
            for tmp in self.outputcolums:
                obj=self.outputcolums[tmp]

                if obj['addnewcolum']=='1': #新增字段

                    sql=f"alter table {self.dbconfig['sourcetable']}  {obj['altervalue'].replace('{colum}',obj['value'])};"
                    print(sql)
                    await self.db.execute(sql)
    async def settaskendflag(self):
        self.sendtaskendflag=1

    async def finish(self):
        self.updateprogresstask.cancel()
        self.historymodel.progress=100
        self.historymodel.endtime=str(datetime.datetime.now())
        await sync_to_async(self.historymodel.save)()
        await self.dingding()
    async def mkgitdir(self,host,conn=None):

        try:
            if not conn:
                conn=await asyncssh.connect(host.ip, port=host.port,username=host.username, password=host.password,known_hosts=None)

            await conn.run('sudo apt install git -y')
            await conn.run('cat /dev/zero | ssh-keygen -q -N "" -f /home/ant/.ssh/id_rsa')
            pub = await conn.run('cat /home/ant/.ssh/id_rsa.pub')
            pubcontent=pub.stdout
            async with asyncssh.connect('49.64.220.49', port=22, username='ant', password='ant@aiwen123',
                                        known_hosts=None) as conn801:
                print(f"grep '{pubcontent[0:-1]}' /home/ant/.ssh/authorized_keys || echo '{pubcontent}'>>/home/ant/.ssh/authorized_keys")
                await conn801.run(f"grep '{pubcontent[0:-1]}' /home/ant/.ssh/authorized_keys || echo '{pubcontent}'>>/home/ant/.ssh/authorized_keys")
            await conn.run('yes | git clone ant@49.64.220.49:/home/ant/lggit lg')
            await conn.run('sh /home/ant/log/installpython.sh')
            await conn.run("sudo /home/ant/conda/bin/pip install asyncssh celery==3.1.26.post2 aioredis supervisor aiodns aiomysql aiohttp dnspython redis==2.10.6 demjson aiodnsresolver -i https://pypi.tuna.tsinghua.edu.cn/simple")
            return 1
        except Exception as e:
            print(e)
            return 0
    async def killremote(self,listname):
        models=Vp.objects.all()
        async def _run(host,lname):
            try:
                print('killremote',host)
                async with asyncssh.connect(host.ip, port=host.port,username=host.username, password=host.password,
                                            known_hosts=None) as conn:

                    tmp=await conn.run(f'sudo pkill -f {lname}')
                    return 1
            except Exception as e:
                print('remoterunerror',e)

        tasks=[_run(host,listname) for host in models]
        await asyncio.wait(tasks)
        redis=await Redis()
        await redis.delete(listname)
        await redis.delete(listname+'_result')

    async def remoterun(self,cmd,hosts=None):
        allhost=Vp.objects.all()
        tmphosts=[host for host in allhost if host.host_id in self.servers]
        try:
            self.historymodel.cmd=cmd
            await sync_to_async(self.historymodel.save)()
        except Exception as e:
            print(e)
        async def _run(host):
            try:
                print('beginremotehost',host)
                async with asyncssh.connect(host.ip, port=host.port,username=host.username, password=host.password,
                                            known_hosts=None) as conn:
                    if host.host_id==801:
                        pass
                    else:
                        tmp=await conn.run('cd /home/ant/lg/scripts/ && git fetch && git reset --hard origin/master')
                    tmp = await conn.run('cd /home/ant/lg')
                    if tmp.returncode!=0:
                        'no lg dirctory create it '
                        if not await self.mkgitdir(conn,host):
                            return {'name': host.host_id, 'status': 1}

                    result = await conn.run(cmd)

                    return {'name': host.host_id, 'status': result.returncode}
            except Exception as e:
                print('remoterunerror',e)
                return {'name': host.host_id, 'status': 2}

        tasks=[_run(host) for host in tmphosts]

        results=await asyncio.wait(tasks)

        dic=[]
        [dic.append(item.result()) for item in results[0]]

        [dic.append({'name':host.host_id,'status':-1}) for host in allhost if host not in tmphosts]
        self.historymodel.vpstatus=json.dumps(dic)
        await sync_to_async(self.historymodel.save)()

    async def startremote(self):
        pass

    async def sendtask(self):
        pass
    async def getresult(self):
        pass
    async def init(self):
        pass
    async def dingding(self):

        try:

            url = 'https://oapi.dingtalk.com/robot/send?access_token=ea60d7a6eb61b92d72f1bf04ebcf2113f12dd0e65e13048760ee14b5f030b907'
            header = {"Content-Type": "application/json", "Charset": "UTF-8"}
            message = {"msgtype": "text", "text": {"content": 'warning: '+self.name+'  完成!!!!'}, "at": {"atMobiles": [self.atmobilesoption[name] for name in self.atmobiles], "isAtAll": False}}
            message_json = json.dumps(message)
            async with aiohttp.ClientSession(headers=header) as session:
                async with session.post(url, data=message_json, timeout=60) as resp:
                    tmpdata = await resp.text()
        except Exception as e:
            print(111, e)

    def run(self):


        self.loop.run_until_complete(self.init())
        self.loop.run_until_complete(asyncio.wait([self.sendtask(),self.getresult(),self.startremote()]))
        self.loop.run_until_complete(self.finish())
        self.loop.run_until_complete(asyncio.wait([self.db.close(),self.redis.close()]))

    async def timerupdateprogress(self):
        while 1:
            self.historymodel.progress = self.progress


            await sync_to_async(self.historymodel.save)()
            await asyncio.sleep(300)
if __name__ == '__main__':
    cls=BaseTask()
    if sys.argv[1]=='inivp':
        try:
            vp=Vp.objects.get(id=int(sys.argv[2]))
            asyncio.run(cls.mkgitdir(vp))
        except Exception as e:
            print(e)
    elif sys.argv[1]=='killtask':
        try:
            asyncio.run(cls.killremote(sys.argv[2]))
        except Exception as e:
            print(e)






