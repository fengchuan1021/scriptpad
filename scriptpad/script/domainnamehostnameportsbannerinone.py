import sys
from pathlib import Path
BASE_DIR = str(Path(__file__).resolve(strict=True).parent.parent.parent)
sys.path.append(BASE_DIR)
from scriptpad import basetask
import threading
class Main(basetask.BaseTask):
    name = "曹松端口探测域名hostnameBanner获取"
    args={'ports':{'name':'ports','alisaname':'要探测的端口','value':'80,443,21,8080,8081','type':'input'},
          'outtable': {'name': 'outtable', 'value': "", 'alisaname': "banner结果输出表", 'formator': '{sourcetable}_banner_{now}'}
          }
    inputcolums = {'ip':{'name': "ip", "value": 'ip'}}
    outputcolums = {'hostname':{'name': "hostname", 'value':'hostname','altervalue': "ADD COLUMN `{colum}` text CHARACTER SET utf8 COLLATE utf8_general_ci NULL",'addnewcolum':'1'},
                    'ports':{'name': "ports", 'value': 'ports', 'altervalue': "ADD COLUMN `{colum}` varchar(1024) NULL DEFAULT NULL", 'addnewcolum': '1'},
                   'domainname':{'name': "domainname", 'value': 'domainname',
                                 'altervalue': "ADD COLUMN `{colum}` text  NULL DEFAULT NULL", 'addnewcolum': '1'},
                    }
    haschildren=1
    def run(self):
        from task.script.hostname import Main as HMain
        from task.script.getipdomainname import Main as DMain
        from task.script.portscan import Main as PMain
        from task.script.banner import Main as BMain
        hostname=HMain()
        domain=DMain()
        port=PMain()
        banner=BMain()
        banner.inputcolums['ports']=port.outputcolums['ports']
        t1=threading.Thread(target=hostname.run)
        t2=threading.Thread(target=port.run)
        t3=threading.Thread(target=domain.run)
        t1.start()
        t2.start()
        t3.start()
        t1.join()
        t2.join()
        t3.join()
        banner.run()
        print( "end?????")




if __name__ == '__main__':
    task=Main()
    task.run()