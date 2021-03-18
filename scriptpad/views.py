from rest_framework.views import APIView
from rest_framework.response import Response
from django.conf import settings
import os,json,psutil
import scriptpad.script as script
import re
import sys
import asyncio
from scriptpad.serializers import historyserializer,TaskSerializer,Vpserializer
from scriptpad.models import TaskHistory
from scriptpad.models import Vp as Vpmodel
if os.name!='nt':
    from crontab import CronTab
from django.db import connections
from rest_framework import viewsets,pagination
import asyncio
import asyncssh
import getpass
class Taskatmobilesoption(APIView):
    def get(self,request):
        from scriptpad.basetask import BaseTask
        arr=BaseTask.atmobilesoption.keys()
        return Response(arr)
class Task(APIView):
    def get(self, request):
        scriptdir=os.path.join(settings.BASE_DIR,'scriptpad','script')
        files=os.listdir(scriptdir)

        tmp=[getattr(script,f[0:-3]).Main.setfilename(f) for f in files if f not in ['__init__.py','__pycache__']]
        scriptarr=sorted(tmp,key=lambda item: item.atmobiles[0] if item.atmobiles else '',reverse=True)

        serializer=TaskSerializer(scriptarr, many=True)
        return Response(serializer.data)
    def post(self,request):
        arr=["ok"]
        print(request.data)
        cmd = sys.executable

        tmp = {f.name: request.data.get(f.name) for f in TaskHistory._meta.fields if f.name in request.data}

        history=TaskHistory(**tmp)
        history.save()
        request.data['taskid']=history.id
        cmd += [os.path.join(settings.BASE_DIR, 'task','script', request.data['filename']), json.dumps(request.data)]
        print(cmd)
        psutil.Popen(cmd)
        cmd[-1]=f"'{cmd[-1]}'"
        if (request.data['cron']['enabled']):
            cron = CronTab(user= getpass.getuser())
            job = cron.new(command=' '.join(cmd),comment='sp'+str(history.id))
            job.setall(request.data['cron']['expression'])
            cron.write()
        return Response(arr)

class TableSearch(APIView):
    def get(self,request):
        tablename=request.query_params.get('sourcetable','')
        sql=f"select table_name,table_schema from information_shema.tables where table_name like '%{tablename}%'"
        arr=[]
        for database in connections:
            try:
                cur=connections[database].cursor()
                cur.execute(sql)
            except Exception as e:

                try:
                    sql = f"show tables like '%{tablename}%'"
                    cur = connections[database].cursor()
                    cur.execute(sql)
                except Exception as e:

                    continue

            tmp=cur.fetchall()
            for t in tmp:
                arr.append({'sourcetable':t[0],'value':f"{database}-{t[0]}",'database':t[1] if len(t)>1 else settings.DATABASES[database]['NAME'],'databaseip':settings.DATABASES[database]['HOST'],'databaseport':settings.DATABASES[database]['PORT'],'databaseuser':settings.DATABASES[database]['USER'],'databasepassword':settings.DATABASES[database]['PASSWORD'],
                            'condition':'','conditionarr':[],'name':database
                            })
        return Response(arr)


class TablePreview(APIView):
    def post(self,request):
        dbconfig=request.data
        obj={'colums':[],'datas':[]}
        if 1:
            db=dbconfig['name']
            cur=connections[db].cursor()
            sql=f"show full columns from  {dbconfig['database']}.{dbconfig['sourcetable']}"
            cur.execute(sql)
            ret=cur.fetchall()
            obj['errortip']='该数据表没有自增id主键请调整'
            obj['colums']=[{"name":row[0]} for row in ret]
            for row in ret:
                if row[0]=='id':
                    if not row[1].startswith('int'):
                        obj['errortip'] = '该数据表id不是int类型请调整'
                        break
                    if row[4]!='PRI':
                        obj['errortip'] = '该数据表id不是主键'
                        break
                    obj['errortip']=''
                    break
            try:
                sql=f"select * from {dbconfig['database']}.{dbconfig['sourcetable']} {dbconfig['condition']} order by id desc limit 5"
                cur.execute(sql)
            except Exception as e:
                sql = f"select * from {dbconfig['database']}.{dbconfig['sourcetable']} {dbconfig['condition']} limit 3"
            print(sql)
            cur.execute(sql)
            ret=cur.fetchall()
            obj['datas']=[{ obj['colums'][i]['name'] :value  for i,value in enumerate(row)} for row in ret]

        return Response(obj)


def killtask(request,taskid,listname):
    from django.http import JsonResponse
    print(taskid,listname)
    try:

        os.system(f"""pkill -f ''taskid": {taskid}'""")
        print(f"""pkill -f '"taskid": {taskid}'""")
        model=Vpmodel.objects.get(id=taskid)
        model.deleteflag=1
        model.save()
    except Exception as e:
        print(e)

    try:
        cmd = sys.executable
        cmd += [os.path.join(settings.BASE_DIR, 'task', 'basetask.py'), 'killtask',listname]
        psutil.Popen(cmd)
    except Exception as e:
        print(e)
    return JsonResponse({'status':'ok'})


class ExamplePagination(pagination.PageNumberPagination):
    page_size = 30
class TaskHistoryviewset(viewsets.ModelViewSet):
    queryset = TaskHistory.objects.all()
    serializer_class = historyserializer
    pagination_class = ExamplePagination
class Vp(viewsets.ModelViewSet):
    serializer_class = Vpserializer
    queryset = Vpmodel.objects.all()
from datetime import datetime
class crontab(APIView):
    http_method_names = ['get', 'put', 'delete']
    def put(self,request,pk):
        cron = CronTab(user= getpass.getuser())
        it = cron.find_comment('sp'+pk)
        item=it.__next__()
        r=item.enable(request.data['status'])
        cron.write()
        msg='禁用' if not r else '启用'
        msg=f'{msg}任务成功'
        return Response({'title':msg,'msg':msg})
    def delete(self,request,pk):
        cron = CronTab(user= getpass.getuser())
        it = cron.find_comment('sp'+pk)
        item=it.__next__()
        item.delete()
        cron.write()
        msg=f'删除任务成功'
        return Response({'title':msg,'msg':msg})
    def get(self, request):
        cron = CronTab(user= getpass.getuser())
        it = cron.find_comment(re.compile(r'sp(\d+)'))
        arr=[]
        for item in it:
            try:
                js=json.loads(item.command.split(' ',2)[2].strip("'"))
                try:
                    sourcetable=js['dbconfig']['sourcetable']
                except Exception as e:
                    sourcetable =''
                try:

                    schedule = item.schedule(date_from=datetime.now())
                    lasttime=schedule.get_prev()
                    nexttime= schedule.get_next()
                    outtable = js['args']['outtable']['value']
                except Exception as e:
                    outtable =''
                arr.append({'name':js['name'],'description':item.description(locale_code='zh_CN'),'enabled':item.is_enabled(),'detail':item.command,'sourcetable':sourcetable,'outtable':outtable,'pk':item.comment[2:],
                            'lasttime':lasttime,
                            'nexttime':nexttime,
                            })
            except Exception as e:
                print(e )
        return Response(arr)



class serverScript(APIView):
    async def readfiles(self,path='.'):
        n=1
        while n<5:
            try:
                async with asyncssh.connect('49.64.220.49', port=22, username='ant', password='ant@aiwen123',
                                            known_hosts=None, keepalive_interval=3) as conn:
                    async with conn.start_sftp_client() as sftp:
                        dirs=await sftp.readdir(path)
                        files=[{'name':f.filename,'isdir':f.longname[0]=='d'} for f in dirs if f.filename!='.']
                        files=sorted(files,key=lambda item:(-item['isdir'],item['name']))
                        return files
            except Exception as e:
                print(e)
                n+=1

    def get(self, request):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result=loop.run_until_complete(self.readfiles())
        return Response(result)