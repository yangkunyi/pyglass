import { boot } from "quasar/wrappers";
import { io } from "socket.io-client";


const socket = io("http://localhost:5020");


// "async" is optional;
// more info on params: https://v2.quasar.dev/quasar-cli/boot-files
export default boot(async ({ app }) => {
  // something to do
  app.config.globalProperties.$socket = socket;
});




export { socket };
