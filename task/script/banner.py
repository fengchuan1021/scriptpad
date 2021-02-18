import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from task import basetask
import netaddr
import ipaddress
import asyncio
import math,json
from task.parsebanner import ParserBanner
class Main(basetask.BaseTask):
    name = "banner采集"
    atmobiles = ['刘亚伟']
    inputcolums={'ip':{'name':"ip","value":'ip'},'ports':{'name':"ports","value":'ports'}}
    args={
               'outtable':{'name': 'outtable', 'value': "", 'alisa': "结果输出表",'formator':'{sourcetable}_banner_{now}'}
    }
    async def startremote(self):
        dic = {"listname": f"{self.tasklist}"}
        print( f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/banner.py '{json.dumps(dic)}'")
        cmd= f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/banner.py '{json.dumps(dic)}'"
        #print(cmd)
        await self.remoterun(cmd)
    async def init(self):

        tabsql=f'''
            CREATE TABLE if not exists `{self.args['outtable']['value']}`  (
                `id` int(11) NOT NULL AUTO_INCREMENT,
                `ip` INT(11) UNSIGNED DEFAULT NULL,
                `port` int(11) NULL DEFAULT NULL,
                 `banner` longtext CHARACTER SET latin1 COLLATE latin1_swedish_ci NULL,
                `service` VARCHAR(512) DEFAULT NULL,
                `version` VARCHAR(32) DEFAULT NULL,
                `orgname` VARCHAR(128) DEFAULT NULL,
                `os` VARCHAR(16) DEFAULT NULL,
                `update_time` datetime(0) NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (`id`) USING BTREE
            ) ENGINE = MyISAM AUTO_INCREMENT = 1 CHARACTER SET = utf8 COLLATE = utf8_general_ci ROW_FORMAT = Dynamic;'''
        #print(tabsql)
        await self.db.execute(tabsql)


    async def sendtask(self):
        sql = f"""select  id from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
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
            print('1sql')
            sql = f"""select id,{self.inputcolums['ip']['value']},{self.inputcolums['ports']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+1000-1} and not (isnull({self.inputcolums['ports']['value']}) or {self.inputcolums['ports']['value']}='') {self.dbconfig['condition'].replace('where','and',1)}"""
            print(sql)
            result=await self.db.execute(sql,1)
            sqlid=sqlid+1000

            arr=[]
            for id,ip,ports in result:

                try:
                    strip=str(ipaddress.ip_address(ip))
                    arr.append(f"{strip}_{ports}")
                except Exception as e:
                    print(e)
            if arr:
                await self.redis.rpush(self.tasklist, *arr)


        await self.settaskendflag()


    async def getresult(self):
        updatesql = f"insert into {self.args['outtable']['value']} (ip,port,banner,service,version,os) values (%s,%s,%s,%s,%s,%s);"

        while 1:
            result = await self.redis.lpop(self.resultlist,encoding="utf-8")
            if result:
                self.sleeptime=0
                ip,port,banner = result.split('_', 2)
                service,version,os=ParserBanner(ip,port,banner).parse()
                await self.db.executemany(updatesql,[[int(ipaddress.ip_address(ip)),port,banner,service,version,os]])
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime>self.maxsleeptime and int(await self.redis.llen(self.tasklist))==0 and int(await self.redis.llen(self.resultlist))==0:

                    break

if __name__ == '__main__':
    task=Main()
    task.run()