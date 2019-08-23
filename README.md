# Grafana-Datasource-Plugin-For-Riverbed-NetIM
  This datasource plugin allows Grafana to submit requests to Riverbed SteelCentral NetIM.
  Use Python Flask environnement server to run the Python script.
  
Request building :
1) Pick source type to query (router, switch or interface)
2) Pick the rollup ('disabled' if request time range is less than 24 hours)
3) Pick source (device or device+interface)
4) Pick metric class
5) Pick metric
6) (optional) Depending of your query, NetIM can return several curves, in order to select one, user must use 'Differenciation' and 'Curve to print' fields. (In older version, this plugin was able to display all of the curves returned in one request, but there was no caption to identify curves).

As of 21 august 2019, this plugin does not suffer from any major known bug.
Line 164 might be tricky, you can replace 250002 by a device id of your own.

More documentation about datasource plugins can be found in the [Docs](https://github.com/grafana/grafana/blob/master/docs/sources/plugins/developing/datasources.md).


## Installation

Add your connexion information in the Python script (credentials, adress, port).

   *Specify your NetIM server's port at the very last line of the script.
   
   *Specify your NetIM server's adresse at line 17.
   
   *Specify your NetIM and PASSWORD at line 18 and 19.
   
Rebuild /dist folder with command ```npm run build```.

Place the folder 'mgent-AppResponse-json-datasource' in your Grafana's plugin folder.

Restart grafana-server.

Run a Python Flask environnement and run the script.


### Dev setup

This plugin requires node 6.10.0

```
npm install -g yarn
yarn install
npm run build
```

### Changelog

1.0.0
- Release

CRINON Nicolas ncrinon@mgen.fr
