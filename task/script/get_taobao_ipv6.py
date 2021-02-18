import sys
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from task import basetask
import asyncio
import json


class Main(basetask.BaseTask):
    name = "获取淘宝ipv6位置数据"
    atmobiles = ['刘金周']
    inputcolums = {'minipv6': {'name': "minipv6", "value": 'minipv6'}}
    args = {
        'outtable': {'name': 'outtable', 'value': "", 'alisaname': "结果输出表", 'formator': 'ljz_ipv6_taobao_{now}'}
    }

    async def init(self):
        tablesql = f'''CREATE TABLE IF NOT EXISTS `{self.args['outtable']['value']}`(
    `id` int(11) NOT NULL AUTO_INCREMENT,
    `ip` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NULL DEFAULT NULL,
    `queryip` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NULL DEFAULT NULL,
    `country` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NULL DEFAULT NULL,
    `region` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NULL DEFAULT NULL,
    `city` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NULL DEFAULT NULL,
    `area` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NULL DEFAULT NULL,
    `isp` varchar(255) CHARACTER SET utf8 COLLATE utf8_bin NULL DEFAULT NULL,
    PRIMARY KEY (`id`) USING BTREE,
    INDEX(`ip`) USING BTREE
    ) ENGINE = MyISAM CHARACTER SET = utf8 COLLATE = utf8_bin ROW_FORMAT = DYNAMIC'''
        print(tablesql)
        await self.db.execute(tablesql)

    async def startremote(self):
        dic = {"listname": f"{self.tasklist}", 'qtype': "CNAME"}
        cmd = f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/get_taobao.py '{json.dumps(dic)}'"
        print(cmd)
        # await self.remoterun(cmd)

    async def sendtask(self):
        sql = f"""select id,{self.inputcolums['minipv6']['value']} from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
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
            sql = f"""select id,{self.inputcolums['minipv6']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+10000-1} {self.dbconfig['condition'].replace('where','and',1)}"""

            result = await self.db.execute(sql, 1)
            sqlid = sqlid + 10000

            arr = []
            for id, minipv6 in result:

                if 1:
                    try:
                        s = f'{id}_{minipv6}'
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

        updatesql = f"insert into {self.args['outtable']['value']} (id,ip,queryip,country,region,city,area,isp) values (%s,%s,%s,%s,%s,%s,%s,%s)"
        print(updatesql)
        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 2000, encoding="utf-8")
            if result:
                self.sleeptime = 0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows = []
                for i in result:
                    rows.append(i.split('_', 7))  # id_infos  just split into 2 length array.
                if rows:
                    await self.db.executemany(updatesql, rows, ignoreerror=True)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime > self.maxsleeptime and int(await self.redis.llen(self.tasklist)) == 0 and int(
                        await self.redis.llen(self.resultlist)) == 0:
                    # await self.finish()
                    break


if __name__ == '__main__':
    task = Main()
    task.run()
