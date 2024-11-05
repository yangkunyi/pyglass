const routes = [
  {
    path: "/",
    component: () => import("layouts/MainLayout.vue"),
    children: [
      {
        path: "rdf",
        name: "rdf",
        component: () => import("layouts/RDFLayout.vue"),
        children: [
          {
            path: "",
            name: "table",
            component: () => import("pages/RDF_table.vue"),
          },
          {
            path: "2",
            name: "2",
            component: () => import("pages/RDF_plot.vue"),
          },
        ],
      },
      {
        path: "",
        name: "view_dm4",
        component: () => import("pages/ViewDM4.vue"),
      },
      {
        path: "calibration",
        name: "calibration",
        component: () => import("layouts/CalibrationLayout.vue"),
        children: [
          {
            path: "center_calibration",
            name: "center_calibration",
            component: () => import("pages/CenterCalibration.vue"),
          },
          {
            path: "elipse_calibration",
            name: "elipse_calibration",
            component: () => import("pages/ElipseCalibration.vue"),
          },
        ],
      },
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: "/:catchAll(.*)*",
    component: () => import("pages/ErrorNotFound.vue"),
  },
];

export default routes;
