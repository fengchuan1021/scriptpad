import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
print(sys.path)
from scriptpad import basetask
import netaddr
import ipaddress
import asyncio
import math, json
from scriptpad.db import Db
import random
import datetime


class Main(basetask.BaseTask):
    name = "验活DNS服务器"
    inputcolums = {'dnsip': {'name': "dnsip", "value": 'NS_IP'}}
    args={
               'outtable':{'name': 'outtable', 'value': "", 'alisaname': "结果输出表",'formator':'DNSServer_allip_open_{now}'}
    }
    dbconfig = {'sourcetable': 'DNSServer_allip', 'databaseip': '192.168.1.32', 'databaseuser': '',
                'databasepasssword': '', 'databaseport': '',
                'condition': '', 'conditionarr': []}

    async def init(self):
        self.args['outtable']['value'] = 'DNSServer_allip_open_' + datetime.datetime.now().strftime('%Y_%m_%d')
        tablesql = f'''CREATE TABLE IF NOT EXISTS `{self.args['outtable']['value']}`  (
          `id` int(11) UNSIGNED NOT NULL AUTO_INCREMENT,
            `NS_IP` varchar(18) NULL,
          `is_open`  tinyint(4) NULL DEFAULT 1,
          `is_rogue`  tinyint(4) NULL DEFAULT 0,
          `last_rtt`  float(6,3) NULL DEFAULT NULL,
          PRIMARY KEY (`id`),
         UNIQUE INDEX `ip`(`NS_IP`) USING BTREE
        ) ENGINE=MyISAM DEFAULT CHARACTER SET=utf8 COLLATE=utf8_general_ci;'''
        await self.db.execute(tablesql)

    async def startremote(self):
        dic = {"listname": f"{self.tasklist}", 'qtype': "VERIFYDNS"}
        cmd = f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/aioquery.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)

    async def sendtask(self):
        sql = f"""select  id,{self.inputcolums['dnsip']['value']} from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        print(sql)
        tmpresult = await self.db.execute(sql, 1)
        if not tmpresult:
            raise ('empty table')
        self.maxid = tmpresult[0][0]
        self.totalnum = self.maxid
        sqlid = 1
        while sqlid <= self.maxid:
            if int(await self.redis.llen(self.tasklist)) > 10000:
                self.progress = (sqlid - 10000) * 100 // self.maxid
                await asyncio.sleep(2)
                continue
            sql = f"""select id,{self.inputcolums['dnsip']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)}"""
            print(sql)
            result = await self.db.execute(sql, 1)
            sqlid = sqlid + 10000

            arr = []
            for id, dnsip in result:

                if 1:

                    try:
                        s = f'{id}_{dnsip}'
                        arr.append(s)
                        if len(arr) >= 3000:
                            print('inserto redis', len(arr), self.tasklist)
                            await self.redis.rpush(self.tasklist, *arr)
                            arr = []
                    except Exception as e:
                        print(e)

            if arr:
                await self.redis.rpush(self.tasklist, *arr)

        await self.settaskendflag()

    async def getresult(self):
        updatesql = f"insert into {self.args['outtable']['value']} (id,NS_IP,is_open) values (%s,%s,%s) ON DUPLICATE KEY UPDATE is_open=VALUES(is_open)"

        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime = 0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows = [i.split('_') for i in result]
                print('getreuslt')
                await self.db.executemany(updatesql, rows)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime > self.maxsleeptime and int(await self.redis.llen(self.tasklist)) == 0 and int(
                        await self.redis.llen(self.resultlist)) == 0:
                    break


if __name__ == '__main__':
    task = Main()
    task.run()
