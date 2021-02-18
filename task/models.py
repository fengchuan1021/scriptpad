from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
# Create your models here.
class TaskHistory(models.Model):
    name=models.CharField(max_length=255,default='')
    sourcetable=models.CharField(max_length=64,default='')
    outtable = models.CharField(max_length=64, default='')
    listname=models.CharField(max_length=255, default='')
    begintime=models.DateTimeField(auto_now_add=True,null=True)
    endtime=models.DateTimeField(null=True)
    progress=models.IntegerField(default=0)
    vpstatus = models.TextField(default='')
    deleteflag=models.IntegerField(default=0)
    cmd=models.TextField(default='')
    class Meta:
       ordering = ['-id']
class Vp(models.Model):
    host_id=models.IntegerField(verbose_name='host_id')
    ip=models.CharField(max_length=16)
    username=models.CharField(max_length=32)
    password=models.CharField(max_length=1024)
    port=models.IntegerField(default=22)

    class Meta:
       ordering = ['-id']

import psutil,os
def afteraddnewvp(sender, instance,created, *args, **kwargs):


    print(instance.id)
    if created:
        try:
            cmd = ["python"] if os.name == "nt" else ["/home/ant/conda/bin/python"]
            cmd+=[os.path.join(settings.BASE_DIR, 'task','basetask.py'), 'inivp',str(instance.id)]
            psutil.Popen(cmd)
        except Exception as e:
            pass
post_save.connect(afteraddnewvp, sender=Vp)