import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
import netaddr
import ipaddress
import asyncio
import math,json
from scriptpad.db import  Db
import random
import datetime
class Main(basetask.BaseTask):
    name = "获取域名NS记录"
    atmobiles = ['刘金周']
    inputcolums = {'domain':{'name': "domain", "value": 'domain'}}
    args={
               'outtable':{'name': 'outtable', 'value': "", 'alisaname': "结果输出表",'formator':'domain_ns_result_{now}'}
    }
    dbconfig = {'sourcetable': '', 'databaseip': '', 'databaseuser': '', 'databasepasssword': '', 'databaseport': '',
                'condition': '', 'conditionarr': []}
    async def init(self):
        tablesql=f'''CREATE TABLE IF NOT EXISTS `{self.args['outtable']['value']}`  (
          `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
          `domain` varchar(255) NULL,
          `ns_record` text NULL,
          `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP,  
          PRIMARY KEY (`id`),
          UNIQUE INDEX `domain`(`domain`) USING BTREE
        );'''
        print(tablesql)
        await self.db.execute(tablesql)
    async def startremote(self):
        dic = {"listname": f"{self.tasklist}",'qtype':"NS"}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/aioquery.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)

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
            sql = f"""select id,{self.inputcolums['domain']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)} group by {self.inputcolums['domain']['value']}"""
            
            result=await self.db.execute(sql,1)
            sqlid=sqlid+10000



            arr=[]
            for id,domain in result:

                if 1:

                    try:
                        s=f'_{domain}'
                        arr.append(s)
                        if len(arr) >= 3000:
                            #print('inserto redis',len(arr),self.tasklist)
                            await self.redis.rpush(self.tasklist, *arr)
                            arr = []
                    except Exception as e:
                        print(e)

            if arr:
                await self.redis.rpush(self.tasklist, *arr)

        await self.settaskendflag()

    async def getresult(self):
        updatesql=f"insert ignore into {self.args['outtable']['value']} (domain,ns_record) values (%s,%s)"


        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime=0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows=[]
                for i in result:
                    domain,record=i.split('_', 1)
                    if record:

                        rows.append([domain,record])
                if rows:
                    await self.db.executemany(updatesql, rows,ignoreerror=True)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break

if __name__ == '__main__':
    task=Main()
    task.run()