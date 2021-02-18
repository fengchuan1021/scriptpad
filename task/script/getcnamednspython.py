import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from task import basetask
import netaddr
import ipaddress
import asyncio
import math,json
from task.db import  Db
import random
import datetime
class Main(basetask.BaseTask):
    name = "获取域名CNAME"
    atmobiles = ['刘金周']
    mark="部分服务器有被封禁现象，最好选择80开头的服务器执行"
    inputcolums = {'domain':{'name': "domain", "value": 'domain'}}
    args={
               'outtable':{'name': 'outtable', 'value': "", 'alisaname': "结果输出表",'formator':'domaincname_{now}'}
    }
    dbconfig = {'sourcetable': '', 'databaseip': '', 'databaseuser': '', 'databasepasssword': '', 'databaseport': '',
                'condition': '', 'conditionarr': []}
    async def init(self):
        tablesql=f'''CREATE TABLE IF NOT EXISTS `{self.args['outtable']['value']}`  (
          `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
          `domain` varchar(100) NULL,
          `cname_record` text NULL,
          `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP,  
          PRIMARY KEY (`id`),
          UNIQUE INDEX `domain`(`domain`) USING BTREE
        );'''
        print(tablesql)
        await self.db.execute(tablesql)
    async def startremote(self):
        dic = {"listname": f"{self.tasklist}",'qtype':"CNAME",'onerecord':'1'}
        cmd=f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/dnspyquery.py '{json.dumps(dic)}'"
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
        updatesql=f"insert ignore into {self.args['outtable']['value']} (domain,cname_record) values (%s,%s)"


        while 1:
            print("开始插入数据")
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                print("已经取到数据")
                print(result)
                self.sleeptime=0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows=[]
                for i in result:
                    domain,cname=i.split('_', 3)[1::2]
                    if cname:
                        cname=json.dumps(cname.split(',')).replace('"',"'") # keep the same formator with previous version.
                        rows.append([domain,cname])
                if rows:
                    print(rows)
                    print("开始执行数据库")
                    await self.db.executemany(updatesql, rows)
                    print("完成")
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break

if __name__ == '__main__':
    task=Main()
    task.run()