import { boot } from "quasar/wrappers";
import { io } from "socket.io-client";

const options = {
  reconnection: true,          // 是否自动重连
  reconnectionAttempts: Infinity, // 最大重连次数
  reconnectionDelay: 1000,     // 初始重连延迟（毫秒）
  reconnectionDelayMax: 5000,  // 最大重连延迟（毫秒）
  timeout: 86400000  ,              // 连接超时时间（毫秒）
};

const socket = io("http://localhost:5000", options);
const socketViewer = io("http://localhost:5000/viewer", options);
const socketRDF = io("http://localhost:5000/rdf", options);
const socketCenCal = io("http://localhost:5000/center_calibration", options)
const socketSim = io("http://localhost:5000/sim",options);
const socketXem = io("http://localhost:5000/xem",options);

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
