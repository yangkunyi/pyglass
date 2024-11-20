import { boot } from "quasar/wrappers";
import { io } from "socket.io-client";

const socket = io("http://127.0.0.1:5000");
const socketViewer = io("http://127.0.0.1:5000/viewer");
const socketRDF = io("http://127.0.0.1:5000/rdf");
const socketCenCal = io("http://127.0.0.1:5000/center_calibration")

// "async" is optional;
// more info on params: https://v2.quasar.dev/quasar-cli/boot-files
export default boot(async ({ app }) => {
  // something to do
  app.config.globalProperties.$socket = socket;
  app.config.globalProperties.$socketViewer = socketViewer;
  app.config.globalProperties.$socketRDF = socketRDF;
  app.config.globalProperties.$socketCenCal = socketCenCal;

});

export { socket,socketViewer,socketRDF,socketCenCal };
