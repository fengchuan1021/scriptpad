<template>
	<div>
		<div v-for="history in historys" style='padding:5px;margin-bottom:10px;border:1px rgb(224,224,224) solid;'>
			<div>
				<span style='display: inline-block;min-width: 300px;'>{{history.name}}</span><span>开始时间:{{history.begintime}}</span>
			</div>
			<div v-if='history.sourcetable'>
			<span v-if='history.sourcetable' style='display: inline-block;min-width: 300px;'>源表:{{history.sourcetable}}</span><span v-if='history.outtable'>输出表:{{history.outtable}}</span>
			</div>
			<div style='height: 30px;'>
				<span :class="history.deleteflag?'delete' :'normal'">队列:{{history.listname}}</span>
				<span style='float: right;margin-right: 20px;'>
					<el-tooltip placement="top">
						<div slot="content">删除任务及远程进程</div>
					<el-button  :type="history.deleteflag?'info' :'primary'" icon="el-icon-delete" size='mini' @click='deletetask(history)'></el-button>
					</el-tooltip>
				</span>
			</div>
			<div style='height: 30px;'>
				<span>命令: {{history.cmd}}</span>
				<span style='float: right;margin-right: 20px;'>
					
					<el-popover
					  placement="bottom"
					  width="400"
					  trigger="click">
					<el-radio-group v-model="radio">
						<el-radio :key=ind v-for='(data,ind) in $store.state.servers' :label='data.host_id' @change="openternimal(history.id,history.cmd)"></el-radio>
					</el-radio-group>
					  
				
					  <el-button slot="reference" :type="history.deleteflag?'info' :'primary'" icon="el-icon-view" size='mini' @click='mcopy(history.cmd)'>调式</el-button>
					 
					</el-popover>
					

					
					<el-tooltip placement="top">
						<div slot="content">复制命令到剪切板</div>
					<el-button  :type="history.deleteflag?'info' :'primary'" icon="el-icon-document-copy" size='mini' @click='mcopy(history.cmd)'></el-button>
					</el-tooltip>
				</span>
			</div>
			<div class='greenarr'>
				
				    <el-tooltip  effect="dark" :content="cacstatus(item)" :key=ind placement="top" v-for="(item,ind) in history.vpstatus">
				      <el-button :type="item.status==0 ? 'success' : item.status==1 ? 'warning' : 'danger'" class='item' size="mini"></el-button>
				    </el-tooltip>
	
			</div>
			<div>
				<el-progress :percentage="history.progress"></el-progress>
			</div>
		</div>
	</div>
</template>
<style>
	.greenarr .item{
		padding:6px;
		margin-left:5px;
	}
</style>
<script>
	import copy from 'copy-to-clipboard';
	  export default {
	    // 2.接收：props接收父组件参数，data1与data2为传递参数的参数名，与父组件内同名
	    props: [],
		created() {
		
		},
		computed:{
			cacstatus(item){
				return function(item){
					return item.name+":"+(item.status==0 ? "执行成功" : item.status==1 ? "python环境缺失" : '连接失败')
				}
				
			},
			
		},
	    data() {
	      return {
			historys:[],radio:''
	      };
	    },

		 methods:{
			 openternimal(id,cmd){
				 
				 this.$emit('switchtab',id,this.radio,cmd);
				 //console.log(id);
				// console.log(this.radio);
			 },
			 mcopy(str){
				 copy(str);
				 console.log(str);
			 },
			 deletetask(history){
				
				this.$axios.get('api/killtask/'+history.id+'/'+history.listname+'/').then(ret=>{
									 console.log(ret.data);
									 history.deleteflag=1;
									 //this.historys=ret.data.results;
				}); 
			 },
			 update(){
				 console.log(1111111);
				 this.$axios.get('api/history/').then(ret=>{
					 console.log(ret.data);
					 this.historys=ret.data.results;
				 });
			 }
			
		 }
	  };
</script>

<style>
	span.delete{
		text-decoration: line-through;
	}
</style>
