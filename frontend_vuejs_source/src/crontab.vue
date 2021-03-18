<template>
<el-row>
	<el-col :span="5">
	<div>
		<el-table :data="datas" style="width: 100%" @current-change="handleTableChange">
			<el-table-column type="index" min-width="5%">
			</el-table-column>
			<el-table-column prop="name" label="名称" min-width="20%">
			</el-table-column>
	
			<el-table-column label="操作" min-width="5%">

				<template slot-scope="scope">
					<el-button size="mini" @click="deletecrontab(scope.$index, scope.row)">X</el-button>
				</template>

			</el-table-column>
		</el-table>
	</div>
</el-col>
	<el-col :span="19">
		<div><el-checkbox v-model="task.enabled" @change='switchcrontab'>启用</el-checkbox></div>
		<div>概况:{{task.description}} 执行</div>
		<div>源表:{{task.sourcetable}}</div>
		<div>输出表:{{task.outtable}}</div>
		
		<div>上次执行时间:{{task.lasttime}}</div>
		<div>下次执行时间:{{task.nexttime}}</div>
		
		<div>命令:{{task.detail}}</div>
		
		
	</el-col>
</el-row>
</template>
<style>

</style>
<script>
	export default {
		// 2.接收：props接收父组件参数，data1与data2为传递参数的参数名，与父组件内同名
		props: [],
	//	components:{myconsole},
		created() {
			
			
			 
		},
		
		computed: {


		},
		data() {
			return {
				task:{enabled:false,},
				datas: [],
		
			};
		},

		methods: {
			handleTableChange(item) {
				
				
				var vue = this;
				if (item==null){
					this.task={enabled:false,};
				}else
				this.task = item;
				
			},
			switchcrontab(nval){
				let pk=this.task.pk;
				this.$axios.put(DOMAIN+'api/crontab/'+pk+'/',{'status':nval}).then(ret=>{
					this.$notify({
						title: ret.data.title,
						type: 'success',
						message:ret.data.msg,
						duration: 5000
					});
				});
			},
			update() {
			
				this.$axios.get(DOMAIN+'api/crontab/').then(ret => {
					this.datas=ret.data;
				
				});
			},
		
			deletecrontab(ind, item) {
				let pk=item.pk;
				console.log(item);
				this.$axios.delete(DOMAIN+'api/crontab/' + pk + '/').then(ret => {
					
					if (ret.status && ret.status == 200) {
						this.datas.splice(ind, 1);
						
						this.task.description='';
						this.task.enabled=false;
						this.task.outtable='';
						this.task.sourcetable='';
						this.task.lasttime='';
						this.task.nexttime='';
						this.task.detail='';
						
		
					this.$notify({
						title: ret.data.title,
						type: 'success',
						message:ret.data.msg,
						duration: 5000
					});

					}

				});
			},


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
</style>
