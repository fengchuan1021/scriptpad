import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
print(sys.path)
from scriptpad import basetask
import netaddr
import ipaddress
import asyncio
import math,json
from scriptpad.db import  Db
import random
import datetime
class Main(basetask.BaseTask):
    name = "用所有DNS获取域名A(ip)记录"
    inputcolums = {'domain':{'name': "domain", "value": 'domain'}}
    args={
               'outtable':{'name': 'outtable', 'value': "", 'alisaname': "结果输出表",'formator':'domainarecord_{now}'}
    }
    dbconfig = {'sourcetable': '', 'databaseip': '', 'databaseuser': '', 'databasepasssword': '', 'databaseport': '',
                'condition': '', 'conditionarr': []}
    async def init(self):
        tablesql=f'''CREATE TABLE IF NOT EXISTS `{self.args['outtable']['value']}`  (
          `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
          `domain` varchar(255) NULL,
          `ip` varchar(16) NULL,
          `dnsip` varchar(32) NULL,  
          `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP,
          PRIMARY KEY (`id`),
          UNIQUE KEY `ddd` (`domain`,`ip`,`dnsip`) USING BTREE
        );'''
        await self.db.execute(tablesql)
    async def startremote(self):
        dic = {"listname": f"{self.tasklist}",'qtype':"A"}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/aioquery.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)
    async def getdns(self):

        if not hasattr(self,'dnsips'):
            table='DNSServer_allip_open_'+(datetime.datetime.now()-datetime.timedelta(days=1)).strftime('%Y_%m_%d')
            db=await Db({'sourcetable': 'DNSServer_allip_open_2020-09-13', 'databaseip': '192.168.1.32', 'databaseuser': 'jiaowei', 'databasepassword': 'jiaowei_123', 'databaseport': 3307,'database':'IPTT',
                    'condition': '', 'conditionarr': []})
            sql=f"SELECT id,NS_IP FROM `{table}` where is_open=1 order by rand()"
            self.dnsips=await db.execute(sql,1)
            await db.close()
        arr=list(self.dnsips)
        random.shuffle(arr)
        return arr


    async def sendtask(self):
        sql = f"""select  id,{self.inputcolums['domain']['value']} from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        print(sql)
        tmpresult=await self.db.execute(sql,1)
        if not tmpresult:
            raise ('empty table')
        self.maxid=tmpresult[0][0]
        self.totalnum=self.maxid
        sqlid=1
        while sqlid<=self.maxid :
            if int(await self.redis.llen(self.tasklist))>10000:
                self.progress=(sqlid-10000)*100//self.maxid
                if self.progress<=0:
                    self.progress=6
                await asyncio.sleep(2)
                continue
            sql = f"""select id,{self.inputcolums['domain']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)}"""
            print(sql)
            result=await self.db.execute(sql,1)
            sqlid=sqlid+10000



            arr=[]
            for id,domain in result:
                tmpdns=await self.getdns()
                for id,ip in tmpdns:

                    try:
                        s=f'{ip}_{domain}'
                        arr.append(s)
                        if len(arr) >= 3000:
                            print('inserto redis',len(arr),self.tasklist)
                            await self.redis.rpush(self.tasklist, *arr)
                            arr = []
                    except Exception as e:
                        print(e)

            if arr:
                await self.redis.rpush(self.tasklist, *arr)

        await self.settaskendflag()

    async def getresult(self):
        updatesql=f"insert into {self.args['outtable']['value']} (ip,dnsip,domain) values (%s,%s,%s) ON DUPLICATE KEY UPDATE ip=VALUES(ip)"


        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime=0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows = [i.split('_', 2) for i in result]

                await self.db.executemany(updatesql, rows)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break

if __name__ == '__main__':
    task=Main()
    task.run()