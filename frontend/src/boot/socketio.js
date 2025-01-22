import { boot } from "quasar/wrappers";
import { io } from "socket.io-client";

const socket = io("http://localhost:5000");
const socketViewer = io("http://localhost:5000/viewer");
const socketRDF = io("http://localhost:5000/rdf");
const socketCenCal = io("http://localhost:5000/center_calibration")
const socketSim = io("http://localhost:5000/sim");
const socketXem = io("http://localhost:5000/xem");

// "async" is optional;
// more info on params: https://v2.quasar.dev/quasar-cli/boot-files
export default boot(async ({ app }) => {
  // something to do
  app.config.globalProperties.$socket = socket;
  app.config.globalProperties.$socketViewer = socketViewer;
  app.config.globalProperties.$socketRDF = socketRDF;
  app.config.globalProperties.$socketCenCal = socketCenCal;
  app.config.globalProperties.$socketSim = socketSim;
  app.config.globalProperties.$socketXem = socketXem;
});

export { socket,socketViewer,socketRDF,socketCenCal,socketSim,socketXem };
