# Grafana-Datasource-Plugin-For-Riverbed-NetIM

This datasource plugin allows Grafana to submit requests to Riverbed SteelCentral NetIM. Use Python Flask environnement server to run the Python script.

Request building :

Pick source type to query (router, switch or interface)

Pick the rollup *'disabled' if request time range is less than 24 hours

if 'disabled' is picked for time range more than 24 hours, average rollup is selected by default

Pick source (device or device+interface)

Pick metric class

Pick metric

(optional) Depending of your query, NetIM can return several curves, in order to select one, user must use 'Differenciation' and 'Curve to print' fields. (In older version, this plugin was able to display all of the curves returned in one request, but there was no caption to identify curves).

As of 21 august 2019, this plugin does not suffer from any major known bug. Line 164 might be tricky, you can replace 250002 by a device id of your own.

Specify your NetIM server's port at the very last line of the script . Specify your NetIM server's adresse at line 17. Specify your USERNAME and PASSWORD line 18 and 19.
