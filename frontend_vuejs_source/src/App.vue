<template>

		
		  <el-tabs  @tab-click='changetable' v-model="chosedtab" >
			  <el-tab-pane label="脚本列表" name="scriptlist">
				  <scriptlist ref="scriptlist"></scriptlist>
			</el-tab-pane>
			<el-tab-pane label="定时记录" name="crontab">
				<crontab ref="crontab"></crontab>
			</el-tab-pane>
			<el-tab-pane label="执行记录" name="scripthistory" >
				<history ref="scripthistory" @switchtab="switchtab"></history>
			</el-tab-pane>
		
			<el-tab-pane label="服务器" name="servers">
				<servers ref="servers"></servers>
			</el-tab-pane>

		</el-tabs>
	
		


  </template>

<script>
	import servers from "./servers";
	import history from "./history";
	import scriptlist from './scriptlist';
	import crontab from './crontab';
	
	
export default {
	 components: {
		  history,
		  servers,
		  scriptlist,
		  crontab,

	    },data() {
	      return {
			chosedtab:'scriptlist',
	      };
	    },

  methods: {
		switchtab(taskid,server,cmd){
			console.log(taskid);
			console.log(server);
			this.chosedtab='servers';
			for(let i=0;i<this.$store.state.servers.length;i++){
				if(this.$store.state.servers[i].host_id==server){
					this.$refs.servers.connect(this.$store.state.servers[i],0,0,0,cmd);
					break;
				}
			}
			
		},
	  changetable(table){
			var tmpname=table.name;
			if (table.name!='scriptlist'){
			  console.log(tmpname);
			  this.$refs[tmpname].update();
			  }
			  
		  
	  },
  }
}
</script>

<style>

</style>
