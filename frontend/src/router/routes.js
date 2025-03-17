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
          {
            path: "RDF_sel",
            name: "RDF_sel",
            component: () => import("pages/RDF_sel.vue"),
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
  {
    path: "/acom",
    name: "ACOM",
    component: () => import("layouts/ACOMLayout.vue"),
    children: [
      {
        path: "",
        name: "Select_Area",
        component: () => import("pages/ACOM/Select_Area.vue"),
      },
      {
        path: "View_Area",
        name: "View_Area",
        component: () => import("pages/ACOM/View_Area.vue"),
      },
      {
        path: "Set_Probe",
        name: "Set_Probe",
        component: () => import("pages/ACOM/Set_Probe.vue"),
      },
      {
        path: "Detect_Bragg_Disks",
        name: "Detect_Bragg_Disks",
        component: () => import("pages/ACOM/Detect_Bragg_Disks.vue"),
      },
      {
        path: "Calibrate_Center",
        name: "Calibrate_Center",
        component: () => import("pages/ACOM/Calibrate_Center.vue"),
      },
      {
        path: "Calibrate_Ellipticity",
        name: "Calibrate_Ellipticity",
        component: () => import("pages/ACOM/Calibrate_Ellipticity.vue"),
      },
      {
        path: "Calibrate_Pixel_Size",
        name: "Calibrate_Pixel_Size",
        component: () => import("pages/ACOM/Calibrate_Pixel_Size.vue"),
      },
      {
        path: "Calculate_ACOM",
        name: "Calculate_ACOM",
        component: () => import("pages/ACOM/Calculate_ACOM.vue"),
      }

    ]

  },
  {
    path: "/sim",
    name: "SIM",
    component: () => import("layouts/DiffSimLayout.vue"),
    children: [
      {
        path: "",
        name: "DiffSim",
        component: () => import("pages/DiffSim/DiffSim.vue"),
      },
    ]
  },
  {
    path: "/xem",
    name: "ACOM VIEWER",
    component: () => import("layouts/AcomViewerLayout.vue"),
    children: [
      {
        path: "",
        name: "AcomViewer",
        component: () => import("pages/ACOM_XEM/ACOM_Viewer.vue"),
      },
    ]
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: "/:catchAll(.*)*",
    component: () => import("pages/ErrorNotFound.vue"),
  },
];

export default routes;
