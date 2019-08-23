import { QueryCtrl } from 'app/plugins/sdk';
import './css/query-editor.css!'

export class GenericDatasourceQueryCtrl extends QueryCtrl {
  constructor($scope, $injector) {
    super($scope, $injector);
    this.scope = $scope;
    // Critical attribute needed in datasource spec (self tests)
    this.target.target = 'unused attribute';
    // All source type available
    this.target.sourceTypeTab = ['Device', 'Interface'];
    // Attribute type correspond to source type (Device or Interface)
    this.target.type = this.target.type;
    // All boolean needed to display correct box (default is Device)
    this.target.displayDeviceBox = this.target.displayDeviceBox;
    this.target.displayInterfaceBox = this.target.displayInterfaceBox;
    // Attribute deviceID is the id of device selected 
    this.target.deviceID = this.target.deviceID;
    // Attribute interfaceID is the id of the interface selected
    this.target.interfaceID = this.target.interfaceID;
    // Attribute metricClassID is the id of metric-class selected
    this.target.metricClassID = this.target.metricClassID;
    // Attribute metricID is the id of metric selected
    this.target.metricID = this.target.metricID || "";
    // Attribute differenciation is the differenciation of the metric selected (can be empty) 
    this.target.differenciation = this.target.differenciation;
    // Depending of target.differenciation, multiple curve can be avalaible to print, user selects one
    this.target.selectedCurve = this.target.selectedCurve;
    // Attribute containing lettre from Grafana row
    this.target.DOMextractedRefID = this.target.DOMextractedRefID;
    this.target.rollupType = this.target.rollupType;
    this.target.rollupTab = ["disabled","aggregateavgrollup","aggregateminrollup","aggregatemaxrollup"];
  }

  // These methods are used by boxes in query.editor.html 
  // Will go to end point '/getDevices' wich retreives all devices avalaible
  getDeviceOptions(query) {
    return this.datasource.metricFindDeviceQuery(query || '');
  }

  // Will go to end point '/getInterfaces' wich retreives all interfaces (from device selected) avalaible and send current grafana query-row letter
  getInterfaceOptions() {
    // Get Grafana row's letter ("A" to Z)
    this.target.DOMextractedRefID = $(document.activeElement).parents("query-editor-row").find(".gf-form-query-letter-cell-letter").text();
    return this.datasource.metricFindInterfaceQuery(this.target.DOMextractedRefID);
  }

    // Will go to end point '/getMetricClasses' wich retreives all metric classes avalaible and send current grafana query-row letter
    getMetricClassOptions() {
      // Get Grafana row's letter ("A" to Z)
      this.target.DOMextractedRefID = $(document.activeElement).parents("query-editor-row").find(".gf-form-query-letter-cell-letter").text();
      // Metric depends of metric class selected, to avoid crash need to reset metric selected
      return this.datasource.metricFindClassQuery(this.target.DOMextractedRefID);
    }
  
    // Will go to end point '/getMetricsOfMetricClass' wich retreives all metrics avalaible for metric class selected and send current grafana query-row letter
    getMetricOptions() {
      // Reset filters to allow NetIM query
      this.target.DOMextractedRefID = $(document.activeElement).parents("query-editor-row").find(".gf-form-query-letter-cell-letter").text();
      // Changing metric change the query, need to reset these 2 attributes
      return this.datasource.metricFindQuery(this.target.DOMextractedRefID || '');
    }

  // Will go to end point '/getDifferenciations' wich retreives all differenciation options avalaible and send current grafana query-row letter
  getDifferenciationOptions() {
    this.target.DOMextractedRefID = $(document.activeElement).parents("query-editor-row").find(".gf-form-query-letter-cell-letter").text();
    // Changing differenciation changes curves avalaible
    return this.datasource.metricFindDifferenciationQuery(this.target.DOMextractedRefID || '');

  }

  // Will go to end point '/getAvailableCurves' wich retreives all curves returned by NetIM and send current grafana query-row letter
  getAvailableCurveOptions() {
    this.target.DOMextractedRefID = $(document.activeElement).parents("query-editor-row").find(".gf-form-query-letter-cell-letter").text();
    return this.datasource.metricFindAvailableCurveQuery(this.target.DOMextractedRefID || '');
  }

  getRollupOptions() {
    this.target.DOMextractedRefID = $(document.activeElement).parents("query-editor-row").find(".gf-form-query-letter-cell-letter").text();
    return this.datasource.metricFindRollupQuery(this.target.DOMextractedRefID || '');
  }

  // When changing source type, bind False to all boolean (all boxes disapear)
  disableAllBoxBool() {
    this.target.displayDeviceBox = false;
    this.target.displayInterfaceBox = false;
  }

  // If source type 'Device' is selected, only his boolean is set to True
  toggleDeviceBool() {
    this.disableAllBoxBool();
    this.target.displayDeviceBox = true;
  }

  // If source type 'Interface' is selected, only his boolean is set to True
  toggleInterfaceBool() {
    this.disableAllBoxBool();
    this.target.displayInterfaceBox = true;
  }

  // Method triggered by source type selection (a new query is being made), cleaning all up
  runningSelect() {
    // Reset attributes
    this.target.deviceID = "";
    this.target.interfaceID = "";
    this.target.metricClassID = "";
    this.target.metricID = "";
    this.target.differenciation = "";
    this.target.selectedCurve = "";
    // Toggling boolean depending of selected case of combobox 'Source type' (this will display concerned boxes):
    if (this.target.type == "Device") {
      this.toggleDeviceBool();
    }
    if (this.target.type == "Interface") {
      this.toggleInterfaceBool();
    }
  }

  // Method triggering /query end point
  onChangeInternal() {
    this.panelCtrl.refresh(); // Asks the panel to refresh data.
  }

  // Debugging purpose
  toString2() {
    console.log("this.target.target " + this.target.target);
    console.log("this.target.type " + this.target.type);
    console.log("this.target.displayDeviceBox : " + this.target.displayDeviceBox);
    console.log("this.target.displayInterfaceBox : " + this.target.displayInterfaceBox);
    console.log("this.target.deviceID : " + this.target.deviceID);
    console.log("this.target.metricID : " + this.target.metricID);
    console.log("this.target.interfaceID : " + this.target.interfaceID);
    console.log("this.target.metricClassID : " + this.target.metricClassID);
    console.log("this.target.differenciation : " + this.target.differenciation);
    console.log("this.target.selectedCurve : " + this.target.selectedCurve);
    console.log("this.target.rollupType : " + this.target.rollupType);
    
  }
}

GenericDatasourceQueryCtrl.templateUrl = 'partials/query.editor.html';

