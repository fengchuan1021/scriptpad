<template>
	<div>
		
	<el-select  v-model='colum' placeholder="请选择"  @change="valchange">
		<el-option
		  v-for="(colum,index) in sourcetablecolums"
		  :key="index"
		  :label="colum.name"
		  :value="colum.name">
		</el-option>
	  </el-select>
	  
	<el-select  v-model='logic' placeholder="请选择" style='width:80px'  @change="valchange"> 
		<el-option
		  v-for="(colum,index) in logicarr"
		  :key="index"
		  :label="colum"
		  :value="colum">
		</el-option>
	  </el-select>
				
	
	<el-input v-model="value" style="width:160px;" @change="valchange"></el-input> 
		
	<el-select  v-model='andor' placeholder="请选择" @change="valchange">
		<el-option
		  v-for="(colum,index) in andorarr"
		  :key="index"
		  :label="colum"
		  :value="colum">
		</el-option>
	  </el-select>
	  <el-button  @click="deleteit">删除</el-button>
	</div>
</template>

<script>
	  export default {
	    // 2.接收：props接收父组件参数，data1与data2为传递参数的参数名，与父组件内同名
	    props: ["sourcetablecolums","conditionindex"],
		created() {
			this.colum=this.sourcetablecolums[0].name;
		},
	    data() {
	      return {
	      'colum':'','logic':'=','andor':'and','value':'','logicarr':['=',">","<","!=",">=","<="],'andorarr':['and','or']
	      };
	    },

		 methods:{
			 valchange:function(){
			
				 this.$emit('onchange',{'colum':this.colum,'logic':this.logic,'andor':this.andor,'value':this.value},this.conditionindex);
			 },
			 deleteit:function(){
				
				 this.$emit('deleteindex',this.conditionindex)
			 }
		 }
	  };
</script>

<style>
</style>
