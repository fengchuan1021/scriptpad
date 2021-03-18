import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
import netaddr
import ipaddress
import asyncio
import math, json
from scriptpad.db import Db
import random
import datetime
from pathlib import Path


class Main(basetask.BaseTask):
    name = "京东万象采集"
    atmobiles = ['刘金周']
    inputcolums = {'ip': {'name': "ip", "value": 'ip'}}
    outputcolums = {'wgs_lat': {'name': "wgs_lat", 'value': 'wgs_lat','altervalue': "ADD COLUMN `{colum}` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL",'addnewcolum': '1'},
                    'wgs_lon': {'name': "wgs_lon", 'value': 'wgs_lon','altervalue': "ADD COLUMN `{colum}` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL",'addnewcolum': '1'},
                    'radius': {'name': "radius", 'value': 'radius','altervalue': "ADD COLUMN `{colum}` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL",'addnewcolum': '1'},
                    'add_time': {'name': "add_time", 'value': 'add_time','altervalue': "ADD COLUMN `{colum}` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL",'addnewcolum': '1'},
                    }

    async def startremote(self):
        dic = {"listname": f"{self.tasklist}", 'qtype': "CNAME"}
        cmd = f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/jdwx.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)

    async def sendtask(self):
        sql = f"""select id,{self.inputcolums['ip']['value']} from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
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
                if self.progress <= 0:
                    self.progress = 6
                await asyncio.sleep(2)
                continue
            sql = f"""select id,{self.inputcolums['ip']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)}"""

            result = await self.db.execute(sql, 1)
            sqlid = sqlid + 10000

            arr = []
            for id, ip in result:

                if 1:
                    try:
                        s = f'{id}_{ip}'
                        arr.append(s)
                        if len(arr) >= 3000:
                            # print('inserto redis',len(arr),self.tasklist)
                            await self.redis.rpush(self.tasklist, *arr)
                            arr = []
                    except Exception as e:
                        print(e)

            if arr:
                await self.redis.rpush(self.tasklist, *arr)

    async def getresult(self):
        lat = self.outputcolums['wgs_lat']['value']
        lon = self.outputcolums['wgs_lon']['value']
        radius = self.outputcolums['radius']['value']
        add_time = self.outputcolums['add_time']['value']

        updatesql = f"insert into {self.dbconfig['sourcetable']} (id,{lat},{lon},{radius},{add_time} ) values (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE {lat}=values ({lat}),{lon}=values ({lon}),{radius}=values ({radius}),{add_time}=values({add_time})"
        print(updatesql)
        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime = 0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows = []
                for i in result:
                    rows.append(i.split('_', 4))  # id_infos  just split into 2 length array.
                if rows:
                    await self.db.executemany(updatesql, rows, ignoreerror=True)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime > self.maxsleeptime and int(await self.redis.llen(self.tasklist)) == 0 and int(
                        await self.redis.llen(self.resultlist)) == 0:
                    await self.finish()
                    break


if __name__ == '__main__':
    task = Main()
    task.run()
