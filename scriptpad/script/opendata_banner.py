import sys
import threading
from pathlib import Path

BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
import asyncio
import json


# def gettables():
#     sql = "select table_name from information_schema.`TABLES` where table_name like 'banner_http%'"
#     tables = db.execute(sql, 1)
#     return tables
# print('lalalalalallalalalalalalallalalalalalal')

class Main(basetask.BaseTask):
    name = "解析opendata离线文件banner信息"
    atmobiles = ['刘金周']
    inputcolums = {'banner': {'name': "banner", "value": 'banner'}}
    outputcolums = {'service': {'name': "service", 'value': 'service',
                                'altervalue': "ADD COLUMN `{colum}` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NULL",
                                'addnewcolum': '1'},
                    'version': {'name': "version", 'value': 'version',
                                'altervalue': "ADD COLUMN `{colum}` varchar(200) CHARACTER SET utf8 COLLATE utf8_general_ci NULL",
                                'addnewcolum': '1'},
                    'os': {'name': "os", 'value': 'os',
                           'altervalue': "ADD COLUMN `{colum}` varchar(40) CHARACTER SET utf8 COLLATE utf8_general_ci NULL",
                           'addnewcolum': '1'},
                    'time': {'name': "time", 'value': 'time',
                             'altervalue': "ADD COLUMN `{colum}` datetime DEFAULT NULL", 'addnewcolum': '1'}}

    # async def innergettables(self):
    #     sql = "select table_name from information_schema.`TABLES` where table_name like 'banner_http%'"
    #     tables = await self.db.execute(sql, 1)
    #     # print(tables, '+++++++++++++++')
    #     return tables
    #
    # async def gettables(self):
    #     return self.loop.run_until_complete(self.innergettables())

    def set_tbname(self, tbname):
        self.dbconfig['sourcetable'] = tbname

    async def startremote(self):
        dic = {"listname": f"{self.tasklist}", 'qtype': "CNAME"}
        cmd = f"sudo /home/ant/conda/bin/python /home/ant/lg/scripts/get_banner.py '{json.dumps(dic)}'"
        print(cmd)
        await self.remoterun(cmd)

    async def sendtask(self):
        # self.dbconfig['sourcetable'] =
        sql = f"""select id,{self.inputcolums['banner']['value']} from {self.dbconfig['sourcetable']} {self.dbconfig['condition']} order by id desc limit 1"""
        # sql = f"""select id,{self.inputcolums['banner']['value']} from {self.tab_name} {self.dbconfig['condition']} order by id desc limit 1"""
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
            sql = f"""select id,{self.inputcolums['banner']['value']} from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+30000-1} {self.dbconfig['condition'].replace('where','and',1)}"""
            # sql = f"""select id,CONCAT(SUBSTRING_INDEX(banner,'\\r\\n\\r\\n',1),'"}}') from {self.dbconfig['sourcetable']} where id between {sqlid} and {sqlid+30000-1} {self.dbconfig['condition'].replace('where','and',1)}"""

            result = await self.db.execute(sql, 1)
            sqlid = sqlid + 30000

            arr = []
            for id, banner in result:

                if 1:
                    try:
                        # real_banner = json.loads(banner)['data']
                        real_banner = json.loads(banner)['data'].split('\r\n\r\n')[0]
                        # 压缩banner
                        # bytes_message = real_banner.encode()
                        # real_banner = zlib.compress(bytes_message, zlib.Z_BEST_COMPRESSION)
                        s = f'{id}|$!$|{real_banner}'
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
        service = self.outputcolums['service']['value']
        version = self.outputcolums['version']['value']
        os = self.outputcolums['os']['value']
        time = self.outputcolums['time']['value']
        updatesql = f"insert into {self.dbconfig['sourcetable']} (id,{service},{version},{os},{time} ) values (%s,%s,%s,%s,%s) ON DUPLICATE KEY UPDATE {service}=values ({service}),{version}=values ({version}),{os}=values ({os}),{time}=values ({time})"
        print(updatesql)
        while 1:
            result = await self.redis.lrange(self.resultlist, 0, 20000, encoding="utf-8")
            if result:
                self.sleeptime = 0
                await self.redis.ltrim(self.resultlist, len(result), -1)
                rows = []
                for i in result:
                    a = i.split('|$!$|', 4)
                    if a[4] == '':
                        a[4] = None
                    rows.append(a)  # id_infos  just split into 2 length array.
                if rows:
                    print("zheng zai ti jiao")
                    await self.db.executemany(updatesql, rows, ignoreerror=True)
            else:
                self.sleeptime += 3
                await asyncio.sleep(3)
                if self.sleeptime > self.maxsleeptime and int(await self.redis.llen(self.tasklist)) == 0 and int(
                        await self.redis.llen(self.resultlist)) == 0:
                    await self.finish()
                    break


if __name__ == '__main__':
    tables = [
        # "banner_http_18080_2020M12_1",
        # "banner_http_3000_2020M12_1",
        # "banner_http_3128_2020M12_1",
        # "banner_http_3689_2020M12_1",
        # "banner_http_4000_2020M12_1",
        # "banner_http_4001_2020M12_1",
        # "banner_http_4040_2020M12_1",
        "banner_http_4567_2020M12_1",
        "banner_http_49152_2020M12_1",
        "banner_http_49153_2020M12_1",
        "banner_http_5000_2020M12_1",
        "banner_http_50880_2020M12_1",
        "banner_http_5431_2020M12_1",
        "banner_http_5555_2020M12_1",
        "banner_http_5984_2020M12_1",
        "banner_http_60000_2020M12_1",
        "banner_http_6060_2020M12_1",
        "banner_http_6066_2020M12_1",
        "banner_http_65535_2020M12_1",
        "banner_http_7000_2020M12_1",
        "banner_http_7001_2020M12_1",
        "banner_http_7010_2020M12_1",
        "banner_http_7011_2020M12_1",
        "banner_http_7077_2020M12_1",
        "banner_http_7100_2020M12_1",
        "banner_http_7547_2020M12_1",
        "banner_http_7548_2020M12_1",
        "banner_http_7549_2020M12_1",
        "banner_http_7678_2020M12_1",
        "banner_http_8000_2020M12_1",
        "banner_http_8001_2020M12_1",
        "banner_http_8008_2020M12_1",
        "banner_http_8060_2020M12_1",
        "banner_http_8080_2020M12_1",
        "banner_http_8081_2020M12_1",
        "banner_http_8088_2020M12_1",
        "banner_http_8181_2020M12_1",
        "banner_http_8500_2020M12_1",
        "banner_http_8545_2020M12_1",
        "banner_http_8761_2020M12_1",
        "banner_http_8820_2020M12_1",
        "banner_http_8888_2020M12_1",
        "banner_http_8899_2020M12_1",
        "banner_http_8983_2020M12_1",
        "banner_http_9000_2020M12_1",
        "banner_http_9001_2020M12_1",
        "banner_http_9002_2020M12_1",
        "banner_http_9060_2020M12_1",
        "banner_http_9200_2020M12_1",
        "banner_http_9990_2020M12_1",
        "banner_http_top1m_2020M12_1",
        "banner_https_10443_2020M12_1",
        "banner_https_11443_2020M12_1",
        "banner_https_12443_2020M12_1",
        "banner_https_1443_2020M12_1",
        "banner_https_16993_2020M12_1",
        "banner_https_2083_2020M12_1",
        "banner_https_2087_2020M12_1",
        "banner_https_2443_2020M12_1",
        "banner_https_3001_2020M12_1",
        "banner_https_30443_2020M12_1",
        "banner_https_40443_2020M12_1",
        "banner_https_4343_2020M12_1",
        "banner_https_4433_2020M12_1",
        "banner_https_4434_2020M12_1",
        "banner_https_4443_2020M12_1",
        "banner_https_44443_2020M12_1",
        "banner_https_4444_2020M12_1",
        "banner_https_49592_2020M12_1",
        "banner_https_5001_2020M12_1",
        "banner_https_50443_2020M12_1",
        "banner_https_50880_2020M12_1",
        "banner_https_5443_2020M12_1",
        "banner_https_55443_2020M12_1",
        "banner_https_60443_2020M12_1",
        "banner_https_6984_2020M12_1",
        "banner_https_7002_2020M12_1",
        "banner_https_7443_2020M12_1",
        "banner_https_7548_2020M12_1",
        "banner_https_7550_2020M12_1",
        "banner_https_8002_2020M12_1",
        "banner_https_8009_2020M12_1",
        "banner_https_8010_2020M12_1",
        "banner_https_8090_2020M12_1",
        "banner_https_8181_2020M12_1",
        "banner_https_8443_2020M12_1",
        "banner_https_8984_2020M12_1",
        "banner_https_9043_2020M12_1",
        "banner_https_9443_2020M12_1",
        "banner_https_top1m_2020M12_1"]

    for i in tables:
        print(11111, i)
        t = Main()
        print(t.dbconfig, "zhi qian ++++++++++++++++++++++++++++++")
        t.set_tbname(i)
        print(t.dbconfig, "zhi hou --------------------------------")
        t1 = threading.Thread(target=t.run)
        t1.start()
        t1.join()

