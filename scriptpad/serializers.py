from rest_framework import serializers
from scriptpad.models import TaskHistory,Vp
import json
class historyserializer(serializers.ModelSerializer):
    vpstatus=serializers.SerializerMethodField()
    begintime= serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", required=False, read_only=True)

    def get_vpstatus(self,obj):
        try:
            return json.loads(obj.vpstatus)
        except Exception as e:
            return {}

    class Meta:
        model =TaskHistory
        fields = "__all__"
class Vpserializer(serializers.Serializer):
    id=serializers.IntegerField(required=False,allow_null=True)
    host_id=serializers.IntegerField(required=True,allow_null=False)
    ip=serializers.CharField(required=True, allow_blank=False, max_length=16)
    username=serializers.CharField(required=True, allow_blank=False, max_length=32)
    password=serializers.CharField(required=True, allow_blank=False, max_length=1024)
    port=serializers.IntegerField(required=True,allow_null=False)
    class Meta:
        model=Vp
        fields = "__all__"

    def create(self, validated_data):
        tmp=Vp.objects.create(**validated_data)
        tmp.save()
        return tmp
#gservers=None
class TaskSerializer(serializers.Serializer):
    name= serializers.CharField(required=True, allow_blank=True, max_length=100)
    mark = serializers.CharField(required=True, allow_blank=True, max_length=300)
    filename = serializers.CharField(required=True, allow_blank=True, max_length=100)
    dbconfig=serializers.DictField()
    args = serializers.DictField()
    inputcolums=serializers.DictField()
    outputcolums=serializers.DictField()
    servers=serializers.ListField()
    cron=serializers.DictField()
    atmobiles=serializers.ListField()

    # atmobilesoption=serializers.SerializerMethodField()
    # def get_atmobilesoption(self,arg):
    #     return arg.atmobilesoption.keys()

    # servers=serializers.SerializerMethodField()
    # def get_servers(self,arg):
    #     global  gservers
    #     if not gservers:
    #         tmp=Vp.objects.all()
    #         data=Vpserializer(tmp,many=True)
    #         return data.data








