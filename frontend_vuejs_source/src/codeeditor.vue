<template>
	
		<codemirror v-model="data" :name='name' :options="cmOptions"/>
	
</template>

<script>
	import { codemirror } from 'vue-codemirror';
	import 'codemirror/lib/codemirror.css';
	import "codemirror/theme/blackboard.css";
	import "codemirror/theme/base16-dark.css";
	import "codemirror/addon/hint/show-hint.css";
	import 'codemirror/mode/python/python.js'
	import "codemirror/addon/hint/show-hint.js"; 
	import "codemirror/addon/lint/lint.css";
	import "codemirror/addon/lint/lint.js"; 
	import "codemirror/addon/lint/json-lint";  
	import "codemirror/addon/fold/foldcode.js"; 
	import "codemirror/addon/fold/foldgutter.js"; 
	import "codemirror/addon/fold/foldgutter.css";
	import "codemirror/addon/fold/brace-fold.js"; 
	import "codemirror/addon/fold/xml-fold.js";
	import "codemirror/addon/fold/comment-fold.js"; 
	import "codemirror/addon/fold/indent-fold.js"; 
	import "codemirror/addon/edit/closebrackets.js"; 
	import "codemirror/addon/edit/closetag.js";
	import "codemirror/addon/edit/matchtags.js"; 
	import "codemirror/addon/edit/matchbrackets.js";
	import "codemirror/addon/selection/active-line.js"; 
	import "codemirror/addon/search/jump-to-line.js"; 
	import "codemirror/addon/dialog/dialog.js";
	import "codemirror/addon/dialog/dialog.css";
	import "codemirror/addon/search/searchcursor.js"; 
	import "codemirror/addon/search/search.js"; 
	import "codemirror/addon/display/autorefresh.js"; 
	import "codemirror/addon/selection/mark-selection.js"; 
	import "codemirror/addon/search/match-highlighter.js";
	
	export default {
	
		  data() {
		    return {
							
		      screenX: 0,
		      screenY: 0,
			  cmOptions: {
			    tabSize: 4,
			    mode: 'python',
			    theme: 'blackboard',
			    lineNumbers: true,
			    line: true,
			  						indentUnit:4,
			  						indentWithTabs:true,
			  						        gutters: ["CodeMirror-linenumbers", "CodeMirror-foldgutter", "CodeMirror-lint-markers"], 
			  								foldGutter: true,
			  								matchBrackets: true, 
			  								autofocus: true,
			  								autoCloseBrackets: true,
			  								styleActiveLine: true,
			  								lineWrapping: true,
			    // more CodeMirror options...
			  }
		    };
		  },
		  props: [
		  	'data',
			'name',
		  ],
	  mounted: function() {
	  //  let myDraggable = this.$refs.myDraggable;
	    //this.initInteract(myDraggable);
	  },
	  components:{codemirror},
 methods: {

    }
	  }
</script>


