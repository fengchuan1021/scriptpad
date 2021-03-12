<template>
<el-row>
	<el-col :span="5">
	<div>
		<div>
			<el-button size='mini' type="primary" :icon='"el-icon-arrow-" +( showform ? "up" : "down")' @click='showform=showform^1'></el-button>
		</div>
		<el-form ref="form" :model="form" :rules="rules" label-position="left" label-width="90px" v-show="showform">
			<el-form-item label="host_id">
				<el-input v-model="form.host_id"></el-input>
			</el-form-item>
			<el-form-item label="ip">
				<el-input v-model="form.ip"></el-input>
			</el-form-item>

			<el-form-item label="username">
				<el-input v-model="form.username"></el-input>
			</el-form-item>


			<el-form-item label="password">
				<el-input v-model="form.password"></el-input>
			</el-form-item>

			<el-form-item label="port">
				<el-input v-model="form.port"></el-input>
			</el-form-item>

			<el-form-item>
				<el-button type="primary" @click="onSubmit">提交</el-button>
			</el-form-item>
		</el-form>


		<el-table :data="$store.state.servers" style="width: 100%" @cell-dblclick="connect">
			<el-table-column prop="host_id" label="host_id">
			</el-table-column>
			<el-table-column prop="ip" label="ip">
			</el-table-column>
			<el-table-column label="操作">

				<template slot-scope="scope">
					<el-button size="mini" @click="deleteserver(scope.$index, scope.row)">X</el-button>

				</template>

			</el-table-column>
		</el-table>
	</div>
</el-col>
	<el-col :span="19">
		<el-tabs  type="card" v-model="editableTabsValue" editable @edit="handleTabsEdit"  >
				  <el-tab-pane
				    :key="index"
				    v-for="(item, index) in connections"
				    
				    
					:name="item.name"
				  >
				  <span slot="label"><i :class="item.status"></i> {{item.name}}</span>
				  <myconsole :item="item" :ref="item.name" @sendmsg='sendmsg($event,item.name)'></myconsole>
				   
				  </el-tab-pane>
		</el-tabs>
		<div>
			<span>命令:</span>
			<el-input style='width: 600px;' v-model="command" id='command'></el-input><el-button size="mini" type='primary' @click='execute'>批量执行</el-button>
		</div>
		<div style='margin-top: 10px;'>
			<el-popover
			  placement="bottom"
			  width="400"
			  trigger="hover" v-for='(item,ind) in serverresult'>
			  <div>{{item.data}}</div>
			<el-button slot="reference" :type="item.status==0 ? 'success' : item.status==-1 ? 'danger' : 'warning'" class='item' size="mini">{{item.name}}</el-button>
			</el-popover>
		</div>
	</el-col>
</el-row>
</template>
<style>

</style>
<script>
	import clone from 'clone';
	import myconsole from './console.vue';
	export default {
		// 2.接收：props接收父组件参数，data1与data2为传递参数的参数名，与父组件内同名
		props: [],
		components:{myconsole},
		created() {
			
			this.update();
			 
		},
		
		computed: {


		},
		data() {
			return {
				command:'',
				serverresult:[],
				socket:'',
				editableTabsValue:'',
				connections:[],
				showform: false,
				datas: [],
				form: {
					host_id: '',
					ip: '',
					username: '',
					password: '',
					port: 22,

				},
				rules: {
					host_id: [{
						required: true,
						message: '请输入服务器host_id',
						trigger: 'blur'
					}, ],
					username: [{
						required: true,
						message: '请输入服务器username',
						trigger: 'blur'
					}, ],
					password: [{
						required: true,
						message: '请输入服务器password',
						trigger: 'blur'
					}, ],
					ip: [{
						required: true,
						message: '请输入服务器ip',
						trigger: 'blur'
					}, ],
					port: [{
						required: true,
						message: '请输入服务器port',
						trigger: 'blur'
					}, ],
				}
			};
		},

		methods: {
			setserverresult(){
				this.serverresult=[];
			
				for(let item of this.$store.state.servers){
					
					this.serverresult.push({'data':'','status':1,name:item.host_id});
				}
			
			},
			execute(){
			
				this.serverresult=[];
				var evtSource = new EventSource('/api/executecommand/'+this.command);
				var vue=this;
				evtSource.onmessage = function(e) {
					let js=JSON.parse(e.data);
					if (js.closed==1){
						console.log('closed');
						evtSource.close();
					}else{
						vue.serverresult.push(js);
					}
				}
				
				
			},
			onSubmit() {
				this.$refs.form.validate((valid) => {
					if (valid) {
						this.$axios.post('/api/vp/', this.form).then(ret => {
							if (ret.data && ret.data.id) {
								let tmp = this.$store.state.servers;
								tmp.unshift(ret.data);
								this.$store.commit('setServers', tmp);
								this.form.host_id = '';
								this.form.ip = '';
								this.$notify({
									title: '添加成功',
									type: 'success',
									message: '添加服务器成功',
									duration: 5000
								});
								this.showform ^= 1;
							}
						});
					} else {

						return false;
					}
				});
			},
			update() {
				this.reconnect();
				this.$axios.get('/api/vp/').then(ret => {
					// console.log(ret.data);
					this.$store.commit('setServers', ret.data.results);
					this.setserverresult();
					//this.datas=ret.data.results;
				});
			},
			findhost(name){
				for(let i=0;i<this.connections.length;i++){
					if(this.connections[i].name==name){
						return this.connections[i];
					}
				}
			},
			readdir(hostname,path){
				 vue.socket.send(JSON.stringify({'action':'readdir','host':hostname,'path':path}));
			},
			reconnect(){
				if(! this.socket){
					this.socket=new WebSocket("ws://"+location.host+"/websocket/");
					var vue=this;
					this.socket.onopen = function()
					   {
						  // Web Socket 已连接上，使用 send() 方法发送数据
						  console.log('connected');
						  vue.socket.send(JSON.stringify({'action':'connect'}));
						  
					   };
					   this.socket.onmessage = function (evt) 
					                  { 
					                     let msg = JSON.parse(evt.data);
										 console.log(msg.action);
										 
										 switch (msg.action){
											 case 'connectsuccess':
											 let tab=vue.findhost(msg.host);
											 tab.status='el-icon-check';
											 break;
											 case 'connectfail':
											 vue.findhost(msg.host).status='el-icon-remove';
											 break;
											 case 'msg':
											console.log('msg.host',msg.host);
											
											 let tmp=vue.$refs[msg.host][0];
											 tmp.myupdate(msg.msg);
											 //vue.findhost(msg.host).content+=msg.msg;
											 break;
											 case 'files':
											 vue.$refs[msg.host][0].setfiles(msg.data);
											 vue.$refs[msg.host][0].currentpath=msg.currentpath;
											 break;
											 case 'filedata':
											 
											 
											 vue.$refs[msg.host][0].setfiledata(msg.data,msg.filename);
											 break;
										 }
										
					                  };
					                   
					  this.socket.onclose = function()
					  { 
						 // 关闭 websocket
						 console.log('closed');
						 vue.socket=undefined;
					  };
					  this.$store.commit('setsocket',this.socket);
				}
			},
			deleteserver(ind, item) {

				this.$axios.delete('/api/vp/' + item.id + '/').then(ret => {
					if (ret.status && ret.status == 204) {
						//this.datas.splice(ind,1);
						let tmp = this.$store.state.servers;
						tmp.splice(ind, 1);
						this.$store.commit('setServers', tmp);
						this.$notify({
							title: '删除成功',
							type: 'success',
							message: '删除服务器成功',
							duration: 5000
						});

					}

				});
			},
 handleTabsEdit(targetName, action) {

			if (action === 'remove') {
			  let tabs = this.connections;
			  let activeName = this.editableTabsValue;
			  if (activeName === targetName) {
				tabs.forEach((tab, index) => {
				  if (tab.name === targetName) {
					let nextTab = tabs[index + 1] || tabs[index - 1];
					if (nextTab) {
					  activeName = nextTab.name;
					}
				  }
				});
			  }
			  
			  this.editableTabsValue = activeName;
			  this.connections = tabs.filter(tab => tab.name !== targetName);
			}
      },
	  sendmsg(data,hostname){
		  var vue=this;
		  console.log('outmsg');
		  console.log(hostname);
		  console.log(data);
	
			  if(vue.socket){
			  			  vue.socket.send(JSON.stringify({'action':'msg','host':hostname,'msg':data}));
		
		  }
		  
	  },
	  connect(item, column, cell, event,cmdstr){
		  let n=0;
		  var tmpitem;
		  function getminname(t){
			  return t.name==''
		  }
		  let inicmd=cmdstr ? cmdstr :'';
		  for(let i=0;;i++){
			  if (! this.connections.find(t=>t.name==item.host_id+(i==0 ? '' :'_'+i))){
				  
				  tmpitem=clone(item);
				  tmpitem['name']=item.host_id+(i==0 ? '' :'_'+i);
				  
				  tmpitem['status']='el-icon-loading';
				  

	  
				  break;
			  }
		  }
		  
		  this.connections.push(tmpitem);
		  this.editableTabsValue=tmpitem.name;
		  this.socket.send(JSON.stringify({'action':'openterminal','host':tmpitem,'inicmd':inicmd})); 
	  }
		}
	};
</script>

<style>
	.el-table td, .el-table th{
		padding:0;
	}
	.el-input {
		width: 200px
	}
	#command{
		
	}
</style>
<style scoped>
	
	.item{margin-left:5px;
	padding:5px;
	}
</style>
