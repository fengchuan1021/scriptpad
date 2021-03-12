<template>
	<el-row>
		<el-col :span="7">
			<div>    <el-radio-group v-model="tmpradio1" size="mini" @change='filterscript'>
			<el-radio-button label="" >全部</el-radio-button>
      <el-radio-button :label="data.text" :key=ind v-for='(data,ind) in filteratmobiles' ></el-radio-button>
     
	
    </el-radio-group></div>
	<div><el-input v-model="serchscript" placeholder="输入脚本名称或文件名搜索" @input='serchscriptchange' clearable></el-input></div>
			<el-table :data="tableData" highlight-current-row @current-change="handleTableChange"  style='width:90%' ref="scripttable">
				<el-table-column type="index" min-width="2%">
				</el-table-column>
				<el-table-column prop="name" label="名称" min-width="78%" filter-placement="bottom-end" :filter-method="filterHandler1">
					<template slot-scope="scope">
					        <el-popover trigger="hover" placement="top">
					          <p>文件名: {{ scope.row.filename }}</p>
					   
					          <div slot="reference" class="name-wrapper">
					            <span>{{ scope.row.name }}</span>
					          </div>
					        </el-popover>
					      </template>
				</el-table-column>
				
				<el-table-column prop="atmobiles" label="负责人" min-width="20%" filter-placement="bottom-end"
				:filters="filteratmobiles" :filter-method="filterHandler" :filter-multiple=false
				>
				</el-table-column>
			<el-table-column prop="filename" label="文件名称" min-width="2%" filter-placement="bottom-end" :filter-method="filterHandler1">
			</el-table-column>
			</el-table>
		</el-col>
		<el-col :span="17">


			<div>
				<label>脚本名称:</label><span>{{task.name}}</span> <label>版本:</label><span>{{task.version}}</span>
			</div>
			<div>
				<h3 style="color:red">{{task.mark}}</h3>
			</div>
			<div>
				<label>源数据表:</label>
				<el-autocomplete class="inline-input" v-model="task.dbconfig.sourcetable" :fetch-suggestions="tablenamesearch"
				 placeholder="请输入内容" :trigger-on-focus="false" @select="sourcetablenameSelect" style='width:500px;'>
				</el-autocomplete>

				<label>源数据库ip:</label><span>{{task.dbconfig.databaseip}}</span></span>

				<label>源数据库端口:</label><span>{{task.dbconfig.databaseport}}</span> </span>
				<label>源数据库:</label><span>{{task.dbconfig.database}}</span> </span>
			</div>



			<h4>数据预览</h4>
			<div style='margin-left: 50px;' v-if="sourcetablecolums">
				<span>筛选原数据表中的数据</span>
				<div><span>sql:</span>{{task.dbconfig.condition}}</div>
				<filtertable v-for="(item,index) in task.dbconfig.conditionarr" :sourcetablecolums="sourcetablecolums" :key="index"
				 :conditionindex="index" @deleteindex="deletecondition" @onchange="conditionvaluechange">
				</filtertable>
				<div>
					<el-button @click="addnewcondition()">
						<添加>
					</el-button>
				</div>
			</div>
			<div style='margin-left: 50px;'>
				<el-table :data="sourcetableData" id='smalltable' border width="100%">
					<el-table-column :key="col.name" :label="col.name" :prop="col.name" :width="calcwidth(col.name)" style='max-width:160px;'
					 v-for="col in sourcetablecolums">
					</el-table-column>

				</el-table>
			</div>



			<div >
				<div><span>要执行的服务器</span>
					<el-button size='mini' @click='xorservers'>反选</el-button>
					<el-button size='mini' @click='selectallservers'>全选</el-button>
				</div>
				<div style='margin-left: 50px;'>
					<el-checkbox-group v-model="task.servers">
						<el-checkbox :key=ind v-for='(data,ind) in $store.state.servers' :label='data.host_id' :keys='ind' :checked=true></el-checkbox>
					</el-checkbox-group>
				</div>

			</div>

			<div v-if="Object.keys(task.args).length" >
				<div>参数</div>
				<div v-for="arg in task.args" style='padding: 5px;margin-left: 50px;'>
					<span>{{arg.alisaname ? arg.alisaname : arg.name}}</span>
					<template v-if="arg.style=='radio'">
						<template v-for="opt in arg.options">
							<el-radio v-model="arg.value" :label="opt.value">{{opt.name}}</el-radio>
						</template>
					</template>
					<el-input v-model="arg.value" maxlength="60" show-word-limit style="width:300px;" v-else>

					</el-input>

				</div>


			</div>

			<div v-if="Object.keys(task.inputcolums).length && sourcetablecolums.length" >
				<div>数据输入</div>

				<div v-for="inputcolum in task.inputcolums" style='padding: 5px;margin-left: 50px;'>
					<div>
						<span>{{inputcolum.name}}<=</span>
						<el-radio v-model="inputcolum.value" :label="colum.name" v-for="(colum,index) in sourcetablecolums" :key=index>{{colum.name}}</el-radio>
					</div>
					<div style='color:red' v-show="sourcetablecolumsarr.indexOf(inputcolum.value)==-1">请选择字段</div>
				</div>



			</div>











			<div v-if="Object.keys(task.outputcolums).length" >
				<div >输出和字段调整</div>
				<div v-for="outputcolum in task.outputcolums" style='margin-left: 50px;'>
					<div style='padding: 5px;'>
						{{outputcolum.name}}
						<el-radio v-model="outputcolum.addnewcolum" label="1">在原表新增字段</el-radio>
						<el-radio v-model="outputcolum.addnewcolum" label="0">使用原有字段</el-radio>

					</div>
					<div v-if="outputcolum.addnewcolum=='1'" style='padding: 5px;'>{{outputcolum.name}}=><el-input v-model="outputcolum.value"
						 style="width:160px;"></el-input>&nbsp;&nbsp;{{dynamicalter(outputcolum)}}</div>
					<div v-if="outputcolum.addnewcolum=='0'" style='padding: 5px;'>
						<el-radio v-model="outputcolum.value" :label="colum.name" v-for="(colum,index) in sourcetablecolums" :key=index>{{colum.name}}</el-radio>

					</div>

				</div>
			</div>

			<div v-if='task.cron' >
			<span><el-checkbox v-model="task.cron.enabled">定时执行</el-checkbox></span>
			<div style='margin-left: 50px;'>
				定时执行条件:<el-input v-model="task.cron.expression"></el-input>(和crontab 定时执行语法一致)

			</div>
			</div>
			
			<div style='margin-top: 20px;'>
				<div>完成后通知:</div>
				<el-checkbox-group v-model="task.atmobiles" style="margin-left:50px">
					<el-checkbox :key=ind v-for='(data,ind) in atmobilesoption' :label='data' :keys='ind'></el-checkbox>
				</el-checkbox-group>
			</div>
			<div style='margin-left: 200px;margin-top: 20px;'>
				<el-button type="primary" @click="begintask" :disabled="disablebutton">开始任务</el-button>
			</div>
		</el-col>
	</el-row>

</template>

<script>
	import {
		DateTime
	} from "luxon";
	import {
		escape
	} from 'sqlstring';
	import filtertable from "./filtertable";
	import servers from "./servers";
	import history from "./history";
	import diff from 'arr-diff';

	export default {
		components: {
			filtertable,
			history,
			servers
		},
		watch: {


			'task.dbconfig.sourcetable'() {
				var now = DateTime.local();
				var tmparr = [];
				this.task.dbconfig.conditionarr.forEach(function(item) {
					tmparr.push(item.value)
				});
				for (var item in this.task.args) {

					console.log(this.task.args[item]);
					if (!this.task.args[item].formator)
						continue
					this.task.args[item].value = this.task.args[item].formator.replace('{sourcetable}', this.task.dbconfig.sourcetable)
						.replace('{now}', now.toFormat('yyyy_MM_dd')).replace('{conditionarr}', tmparr.join('_'));
						if(this.task.args[item].value.length>62)
						this.task.args[item].value=this.task.args[item].value.substring(0,62)
				}
			},
			'task.dbconfig.condition'() {
				var now = DateTime.local();
				var tmparr = [];
				this.task.dbconfig.conditionarr.forEach(function(item) {
					tmparr.push(item.value)
				});
				for (var item in this.task.args) {

					if (!this.task.args[item].formator)
						continue
					this.task.args[item].value = this.task.args[item].formator.replace('{sourcetable}', this.task.dbconfig.sourcetable)
						.replace('{now}', now.toFormat('yyyy_MM_dd')).replace('{conditionarr}', tmparr.join('_'));
				}
			}
		},
		computed: {
			dynamicalter(colum) {
				return function(colum) {

					return colum.altervalue.replace("{colum}", colum.value);
				}

			},

			calcwidth(name) {
				return function(name) {
					var lowname = name.toLowerCase();
					if (lowname.indexOf('id') !== -1) {
						return "70px";
					}
				}
			}
		},
		data: function() {
			return {
				serchscript:'',
				tmpradio1:'',
				tableData: [],
				disablebutton: false,
				atmobilesoption:[],
				filteratmobiles:[],
				task: {
					dbconfig: {
						'sourcetable': '',
						conditionarr: []
					},
					'args': {},
					'inputcolums': {},
					'outputcolums': {},
					'servers': [],
					'atmobiles':[],
				},
				sourcetablecolums: [],
				sourcetableData: [],
				activetable: 'scriptlist',
				sourcetablecolumsarr: []

			}
		},
		mounted() {
			this.$axios.get("/api/Taskatmobilesoption/").then(ret=>{
				this.atmobilesoption=ret.data;
				this.atmobilesoption.forEach(item=>this.filteratmobiles.push({'text':item,'value':item}));
				console.log(this.filteratmobiles);
				this.$axios.get("/api/task/").then(ret => {
				
					this.tableData = ret.data;
				});
				
			});
			

		},

		methods: {
			serchscriptchange(value){
				console.log(this.serchscript);
				for (let e of this.$refs.scripttable.columns){
					if(e.property=='name'){
				
						if (this.serchscript=='')
						e.filteredValue=[];
						else
						e.filteredValue=[this.serchscript];
				this.$refs.scripttable.store.commit('filterChange', {
				    column: e,
				    values:e.filteredValue,
				  });
				  this.$refs.scripttable.store.updateAllSelected();
						break;
					}
				}
			},
			filterHandler1(value, row, column){
			
				return row.name.indexOf(value)!=-1 || row.filename.indexOf(value)!==-1;
				
			},
			filterHandler(value, row, column){
			
				return row.atmobiles[0]==value;
				
			},
			filterscript(value){
				for (let e of this.$refs.scripttable.columns){
					if(e.property=='atmobiles'){

						if (value=='')
						e.filteredValue=[];
						else
						e.filteredValue=[value];
				this.$refs.scripttable.store.commit('filterChange', {
				    column: e,
				    values:e.filteredValue,
				  });
				  this.$refs.scripttable.store.updateAllSelected();
						break;
					}
				}
			
				
			},
			xorservers() {
				let tmparr = [];
				this.$store.state.servers.forEach(function(item) {
					tmparr.push(item.host_id)
				});
				let tmp = diff(tmparr, this.task.servers);

				this.task.servers = tmp;
			},
			selectallservers() {
				let tmparr = [];
				this.$store.state.servers.forEach(function(item) {
					tmparr.push(item.host_id)
				});
				this.task.servers = tmparr;
			},
			changetable(table) {
				var tmpname = table.name;
				if (table.name != 'scriptlist') {
					console.log(tmpname);
					this.$refs[tmpname].update();
				}


			},
			updatecondition() {
				var s = 'where ( ';
				for (let i = 0; i < this.task.dbconfig.conditionarr.length; i++) {
					var item = this.task.dbconfig.conditionarr[i];
					s += item.colum + " " + item.logic + " " + escape(item.value) + " ";
					if (i != this.task.dbconfig.conditionarr.length - 1) {
						s += item.andor + " ";
					}


				}
				this.task.dbconfig.condition = this.task.dbconfig.conditionarr.length ? s + ')' : '';
				this.previewtable();

			},
			conditionvaluechange(obj, ind) {
				this.task.dbconfig.conditionarr[ind] = obj;



				this.updatecondition();

			},
			addnewcondition() {
				this.task.dbconfig.conditionarr.push({});
			},
			deletecondition(index) {

				this.task.dbconfig.conditionarr.splice(index, 1);

				this.updatecondition();

			},
			begintask() {
				// this.disablebutton=true;
				if (!this.task.filename) {
					this.$alert("请选择要执行的脚本");
					return false;
				}
				if (!this.task.dbconfig.sourcetable) {
					this.$alert("未选择数据表");
					return false;
				}

				for (let j in this.task.inputcolums) {
					if (this.sourcetablecolumsarr.indexOf(this.task.inputcolums[j].value) == -1) {
						this.$alert("有输入字段未选择");
						return false;
					}
				}

				for (let j in this.task.outputcolums) {
					console.log(this.task.outputcolums[j].addnewcolum);
					if (this.task.outputcolums[j].addnewcolum == '0' && this.sourcetablecolumsarr.indexOf(this.task.outputcolums[j].value) ==
						-1) {
						this.$alert("有输出字段未选择");
						return false;
					}
				}


				this.$axios.post("/api/task/", this.task).then(ret => {
					this.$notify({
						title: '成功',
						type: 'success',
						message: '发布任务成功',
						duration: 3000
					})
				});




			},
			previewtable() {
				this.$axios.post("/api/tablepreview/", this.task.dbconfig).then(ret => {
					this.sourcetablecolums = ret['data']['colums'];
					this.sourcetablecolumsarr = [];
					var tmparr = this.sourcetablecolumsarr;
					this.sourcetablecolums.forEach(function(item, index) {
						tmparr.push(item.name);

					});
					for (let i in this.task.outputcolums) {

						if (tmparr.indexOf(this.task.outputcolums[i].value) !== -1) {
							this.task.outputcolums[i].addnewcolum = '0';
						}
					}

					this.sourcetableData = ret['data']['datas'];
					if (ret['data']['errortip']){
						this.$alert(ret['data']['errortip']);
					}
				});
			},
			sourcetablenameSelect(item) {
				delete item['value'];
				this.task.dbconfig = item;
				this.previewtable();

			},
			tablenamesearch(queryString, cb) {
				this.$axios.get('/api/tablesearch/?sourcetable=' + this.task.dbconfig.sourcetable).then(ret => {
					cb(ret.data);
				});


			},
			handleTableChange(item) {
				var vue = this;
				this.task = item;
				
				this.task.servers = this.$store.state.servers.map(function(item) {
					return item.host_id
				});
				console.log(this.task.servers);
				if (this.task.dbconfig.sourcetable)
					this.tablenamesearch(this.task.dbconfig.sourcetable, function(data) {
						vue.sourcetablenameSelect(data[0])
					});
			},

		}
	}
</script>

<style>
	#app {
		font-family: Helvetica, sans-serif;
		text-align: center;
	}
.el-autocomplete .el-input{
	width: 400px;
}
	#smalltable {
		line-height: 11px;
		padding: 3px;
		padding-left: 1px;
	}

	#smalltable .cell {
		line-height: 11px;
		padding-left: 1px;
		padding-right: 1px;
		height: 15px;
		word-break: keep-all;
		text-overflow: unset;
		overflow-x: scroll;
	}

	#scripttable .el-table__body {
		width: 80%;
	}
.el-table_1_column_4 {display: none;}
	#smalltable .cell::-webkit-scrollbar {
		display: none;
	}
</style>
