<template>
<div>
	
	
	<div class="console" :id="item.name" style="height: 600px;width: 100%;">
		
	</div>

</div>	
</template>

<script>
	import {
		Terminal
	} from 'xterm';
	
	
	
	import {
		FitAddon
	} from 'xterm-addon-fit';
	import 'xterm/css/xterm.css';
	import codeeditor from './codeeditor.vue'

	export default {
		components:{codeeditor},

		methods: {
		
			myupdate(msg) {
				this.term.write(msg);
			},
			setfiles(files){
				
				this.files=files;
			},
			setfiledata(data,filename){
				
				for(let i=0;i<this.openfiles.length;i++){
					if(this.openfiles[i].filename==filename)
					this.openfiles[i].content=data;
					break;
				}
				
			},
			editfile(index,item){
				
			},
			readdir(dirname){
				console.log(this.$parent);
				this.$store.state.socket.send(JSON.stringify({'action':'readdir','host':this.item.name,'path':this.currentpath+'/'+dirname}));
				
			},
			editfile(filename){
				let tmp={};
				tmp.filename=this.currentpath+'/'+filename;
				this.$store.state.socket.send(JSON.stringify({'action':'readfile','host':this.item.name,'path':tmp.filename}));
				tmp.content='loading.......';
				this.openfiles.push(tmp);
			},
			openfile(item, column, cell, event){
				if(item.isdir){
					this.readdir(item.filename);
				}else{
					this.editfile(item.filename);
				}
			}
		},
		data() {
			return {
	
				'openfiles':[],
				'currentpath':'.',
				'files':[],
				'term': null,
				fitadd: null,
				lastcommand:'',

			}
		},
		props: [
			'item',
		],

		mounted() {
	
			let terminalContainer = document.getElementById(this.item.name);
			this.term = new Terminal({
				fontSize: 14,
				cursorBlink: true
			});
			this.fitadd = new FitAddon();
			this.term.loadAddon(this.fitadd);
			this.term.open(terminalContainer);
			this.fitadd.fit();
			var vue=this;
			this.term.onData(function(data){
					vue.$emit('sendmsg',data);
					
				
			});
			this.term.onKey((key, ev) => {
					
			       
					if(key.domEvent.code=='Enter'){
						if (vue.lastcommand=='ls' || vue.lastcommand=='ll'){
							console.log('hook ls');
						}
						vue.lastcommand='';
						//vue.term.write('\n');
					}else{
						vue.lastcommand+=key.key;
					}

			});
			//this.fitadd.fit();
		},

		beforeDestroy() {
			
			this.term.dispose();
		}

	}
</script>

<style>

	.el-table td, .el-table th{
		padding:0;
	}
	.console{
		float:left;
		display: inline-block;
	}
	.filelist{
		display: inline-block;
	}

</style>

