import Vue from 'vue'
import Vuex from 'vuex'
Vue.use(Vuex)
export default new Vuex.Store({
  state: {
    servers:[],
	socket:null,
  },
  mutations: {
	setServers(state,nservers){
		state.servers=nservers;
	},
	setsocket(state,nsocket){
		state.socket=nsocket;
	}
  },
  actions: {
 
  },
  getters:{
	  servers:state=>state.servers,
	  socket:state=>state.socket,
  }
})　　