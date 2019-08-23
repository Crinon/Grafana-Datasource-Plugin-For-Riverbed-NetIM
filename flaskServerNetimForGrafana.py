import requests
import json
import time
import string
from flask import Flask
from flask import jsonify
from flask import request
from calendar import timegm
from datetime import datetime
# Lines containing critical informations : 17 18 19 + very last line (port)
#########################################################################################################################
##                                                                                                                     ##
##                                                 Initializing server                                                 ##
##                                                                                                                     ##
#########################################################################################################################
# Riverbed NetIM's address and credentials
HOST = ""
USERNAME = ""
PASSWORD = ""
basicHttpAuth = 'https://'+USERNAME+':'+PASSWORD+'@'+HOST+'/api/netim'

# Creating instance of Flask (e.g app)
serverFlask = Flask(__name__)
# Session is used for SSL overriding
session = requests.Session()

# Device list does not depend of any informations, buffered for a limited time
# Time in seconds to keep alive device list in buffer
globalDeviceListTimeAllowed = 600
# Time in seconds for testing time between last function call and current time
globalLastTimeDevicesListHasBeenPicked = 0
# Initialize list
globalDevicesList = []

# Metric classes list does not depend of any informations, buffered for a limited time
# Time in seconds to keep alive metric classes list in buffer
globalMetricClassListTimeAllowed = 600
# Variable for buffering process
globalLastTimeMetricClassesListHasBeenPicked = 0
# Initialize list
globalMetricsClassesList = []

globalAllCurves = {}
globalReadableDeviceDict = {}

# List containing all deviceId currently used, list initialized to 0 on 26 positions
global_allRow_deviceID = [0]*26
# List containing all interfaceId currently used, list initialized to 0 on 26 positions
global_allRow_interfaceID = [0]*26
# List containing all metrics of metric class currently used, list initialized to 0 on 26 positions
global_allRow_metricsIdOfMetricClass = [0]*26
# To compare currentMetric in samples and add in differenciation list, list initialized to 0 on 26 positions
# Readable because we want description and id
global_allRow_readableMetricDict = [0]*26
global_allRow_differenciationOptionsList = [0]*26
# # List containing all metric classes avalaible, list initialized to 0 on 26 positions
global_allRow_metricClassID = ['']*26

# List with all curves name (the name picked will be used in dictionnary variable globalAllCurves)
global_allRow_availableCurvesList = [0]*26

#########################################################################################################################
##                                                                                                                     ##
##                                              FUNCTIONS DECLARATION                                                  ##
##                                                                                                                     ##
#########################################################################################################################
# POST request function (creation of report)
# Argument dataDefsJSON = data definitions in JSON format (=metric query)
def requestData(urlIN, dataDefsJSON):
    headers={"content-type":"application/json"}
    r = session.post(urlIN, dataDefsJSON, headers=headers, verify=False)
    return r


# GET request function (collect informations through API : hostgroups, applications, webapps...)
# Argument url = API's url
def retrieveInformationFromAPI(urlIN):
    r = session.get(urlIN, verify=False)
    return r


# Time converting to epoch time format (seconds elapsed from 1970)
def convert_to_epoch(timestamp):
    return timegm(datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%S.%fZ').timetuple())


#########################################################################################################################
##                                                                                                                     ##
##                                                     HEALTH TEST                                                     ##
##                                                                                                                     ##
#########################################################################################################################
# Response when adding new datasource in Grafana, must return a 200 http_code to be accepted
@serverFlask.route("/", methods = ['GET'])
def healthTest():
    return "OK"


#########################################################################################################################
##                                                                                                                     ##
##                                              DEVICES LIST RETRIEVING                                                ##
##                                                                                                                     ##
#########################################################################################################################
# Device list is big and does not depend of any id, keep-alive for 120 seconds
# Function set 2 major variables : list of all device ID and all device with id and readable name
@serverFlask.route("/getDevices", methods = ['POST'])
def getDevices():
    global globalLastTimeDevicesListHasBeenPicked
    global globalDevicesList
    global globalReadableDeviceDict

    # If it has been less than "globalDeviceListTimeAllowed" seconds since the last creation of the globalDevicesList
    # no query is made to Riverbed's API and the list sent is in buffer
    timeIsDevicesListOutdated = round((time.time() - globalLastTimeDevicesListHasBeenPicked),0)
    if timeIsDevicesListOutdated < globalDeviceListTimeAllowed :
        return jsonify(globalDevicesList)
    # Else create a new fresh list
    else :
        # API for devices retrieving
        urlGET = basicHttpAuth+'/v1/devices'
        # Retrieving devices list
        response = retrieveInformationFromAPI(urlGET)
        # Making a dict to easly access to the listing part
        dictionnaire = json.loads(response.text)
        # Field 'items' contains all devices (name and id)
        allDevices = dictionnaire['items']
        # Dict for readable caption (display displayName instead of device's id)
        globalReadableDeviceDict = {}
        # Reset list
        globalDevicesList= []
        # For each device add object{name, id} (JS will interpret it, user clicks on name but JS retrieves id) 
        for device in allDevices:
            globalDevicesList.append({'text': device["name"], 'value':str(device['id'])})
            globalReadableDeviceDict[str(device['id'])]= str(device["displayName"])
    # Save time device list has been created
    globalLastTimeDevicesListHasBeenPicked = time.time()
    return jsonify(globalDevicesList)

#########################################################################################################################
##                                                                                                                     ##
##                                             INTERFACES LIST RETRIEVING                                              ##
##                                                                                                                     ##
#########################################################################################################################

@serverFlask.route("/getInterfaces/<grafanaRowLetter>", methods = ['GET'])
# Var grafanaRowLetter is send by plugin via HTTP GET, it's a single char, from A to Z (Grafana row's letter)
def getInterfaces(grafanaRowLetter):
    global global_allRow_deviceID
    global global_allRow_interfaceID

    # Convert value to lowercase
    currentRowLetter = grafanaRowLetter.lower()
    # Convert value to index in alplhabet (A is 0 and Z is 25)
    currentRowNumber = string.lowercase.index(currentRowLetter)
    # Retrieving deviceId belonging to current row
    currentRowDeviceID = global_allRow_deviceID[currentRowNumber]
    
    # API for interfaces retrieving, variable is deviceID from row selected
    urlGET = basicHttpAuth+'/v1/devices/'+str(currentRowDeviceID)+'/interfaces'

    # Retrieving interfaces list
    response = retrieveInformationFromAPI(urlGET)
    # When openning page, error may occur, this counter that error (causing unwanted trouble)
    if(response == 404) :
        urlGET=basicHttpAuth+'/v1/devices/250002/interfaces'
        response = retrieveInformationFromAPI(urlGET)

    # Making a dict to easly access to the listing part
    dictionnaire = json.loads(response.text)
    
    try:
        # Field 'items' contains all interfaces (name and id)
        allInterface = dictionnaire['items']
    # If there is a problem with the deviceId, ask to pick another (occurs if no interface belongs to device)
    except KeyError as e:
        dictionnaire = {'items': [{'name':  'please repick device', 'id': '0'}]}
        allInterface = dictionnaire['items']

    # Variable containing all interfaces belonging to device from row 
    interfacesList= []
    # For each interfaceed, add object{name, id} (JS will interpret it, user click on name but JS retrieves id) 
    for interface in allInterface:
        interfacesList.append({'text': interface["name"], 'value':str(interface['id'])})

    global_allRow_interfaceID[currentRowNumber] = interfacesList
    return jsonify(global_allRow_interfaceID[currentRowNumber])


#########################################################################################################################
##                                                                                                                     ##
##                                          METRICS LIST RETRIEVING                                                    ##
##                                                                                                                     ##
#########################################################################################################################
# Metric-classes list is big and does not depend of any id, keep-alive for 120 seconds
@serverFlask.route("/getMetricClasses", methods = ['POST'])
def getMetricClasses():
    global globalLastTimeMetricClassesListHasBeenPicked
    global globalMetricsClassesList  

    # Retrieving JSON from Grafana in order to extract row letter (and number)
    grafanaData = request.get_json()

    # Letter from Grafana's row (converted to integer, alphabetical position)
    currentRowLetter = grafanaData['target'].lower()
    currentRowNumber = string.lowercase.index(grafanaData['target'].lower())

    # If user clicked on metric
    global_allRow_availableCurvesList[currentRowNumber] = []

    # If it has been less than 4 seconds since the last creation of the globalMetricsClassesList, no query is made to Riverbed's API
    timeIsMetricClassesListOutdated = round((time.time() - globalLastTimeMetricClassesListHasBeenPicked),0)
    if timeIsMetricClassesListOutdated < 120 :                
        return jsonify(globalMetricsClassesList)
    else :
        # API for devices retrieving
        urlGET = basicHttpAuth+'/v1/metric-classes'
        # Retrieving devices list
        APIinformations = retrieveInformationFromAPI(urlGET)
        # Making a dict to easly access to the listing part
        dictionnaire = json.loads(APIinformations.text)
        # Field 'items' contains all host groups (name and id)
        allMetricClass = dictionnaire['items']
        globalMetricsClassesList= []
        # For each host group, if enabled, add object{name, id} (angular will interpret it, user click on name but JS retrieves id) 
        for metricClass in allMetricClass:
            globalMetricsClassesList.append({'text': metricClass["name"], 'value':str(metricClass['id'])})    
        
        globalLastTimeMetricClassesListHasBeenPicked = time.time()
        return jsonify(globalMetricsClassesList)        

# Metrics for metric-class selected
@serverFlask.route("/getMetricsOfMetricClass", methods = ['POST'])
def getMetricsOfMetricClass():
    global global_allRow_readableMetricDict
    global global_allRow_metricClassID
    global global_allRow_metricsIdOfMetricClass


    # Retrieving JSON from Grafana in order to extract row letter (and number)
    grafanaData = request.get_json()

    # Space added in first position, position [1] is the letter from Grafana's row
    currentRowLetter = grafanaData['target'].lower()
    currentRowNumber = string.lowercase.index(grafanaData['target'].lower())

    # If metric class has been correctly picked first
    if grafanaData['target'] != '' :
        # API for metric classes retrieving
        urlGET = basicHttpAuth+'/v1/metric-classes/'+str(global_allRow_metricClassID[currentRowNumber])
    # If no metric class has been picked
    else :
        # Use fake url to avoid unnecessary query that overloads NetIM server (cause 404 error)
        urlGET = basicHttpAuth+'/v1/metric-classes/null'

    # Retrieving devices list
    APIinformations = retrieveInformationFromAPI(urlGET)

    if APIinformations.status_code == 204 :
        return jsonify({'text': 'please repick metric class', 'value':0})

    # Making a dict to easly access to the listing part
    dictionnaire = json.loads(APIinformations.text)
    
    try:
        # Field 'items' contains all host groups (name and id)
        allMetric = dictionnaire['metrics']['items']
    # If there is a problem with the deviceId, ask to pick another (occurs if no interface belongs to device)
    except KeyError as e:
        return jsonify({'text': 'please repick metric class', 'value':0})

    metricsList= []
    global_allRow_readableMetricDict[currentRowNumber] = {}

    # For each host group, if enabled, add object{name, id} (angular will interpret it, user click on name but JS retrieves id) 
    for metric in allMetric:
        if metric["name"] != None :
            global_allRow_readableMetricDict[currentRowNumber][str(metric['id'])] = str(metric["name"])
        else :
            global_allRow_readableMetricDict[currentRowNumber][str(metric['id'])] = str(metric["description"])

        # If field 'units' exists
        try:
            # If field 'units' is set to None, units is occurence
            if metric["units"] is None:
                metricsList.append({'text': metric["displayName"]+'   (occurence)', 'value':str(metric['id'])})
            # If field 'units' is not None, units is metric["units"]
            else :
                # timestamp field is irrevelant
                if metric["id"] != "timestamp" and metric["id"] != "duration" and metric["displayName"] !='none':
                    metricsList.append({'text': metric["displayName"]+"   ("+metric["units"]+")", 'value':str(metric['id'])})
        # If field 'units' does not exist, units is (no unit)
        except KeyError as e:
            metricsList.append({'text': metric["displayName"]+"   (no unit)", 'value':str(metric['id'])})
    
    global_allRow_availableCurvesList[currentRowNumber] = []
    global_allRow_metricsIdOfMetricClass[currentRowNumber] = metricsList
    return jsonify(global_allRow_metricsIdOfMetricClass[currentRowNumber])


#########################################################################################################################
##                                                                                                                     ##
##                                                    FILTER CHOICE                                                    ##
##                                                                                                                     ##
#########################################################################################################################

@serverFlask.route("/getDifferenciations", methods = ['POST'])
def getDifferenciations():
    global global_allRow_differenciationOptionsList
    # Retrieving JSON from Grafana in order to extract row letter (and number)
    grafanaData = request.get_json()
    # Letter from Grafana's row
    currentRowLetter = grafanaData['target'].lower()
    # Letter's position in alphabet for list positionning
    currentRowNumber = string.lowercase.index(grafanaData['target'].lower())
    if not global_allRow_differenciationOptionsList[currentRowNumber] :
        return jsonify(['ERROR : User did not build any query'])
    else :
        return jsonify(global_allRow_differenciationOptionsList[currentRowNumber])

@serverFlask.route("/getAvailableCurves", methods = ['POST'])
def getAvailableCurves():
    global global_allRow_availableCurvesList
    # Retrieving JSON from Grafana in order to extract row letter (and number)
    grafanaData = request.get_json()
    # Letter from Grafana's row
    currentRowLetter = grafanaData['target'].lower()
    # Letter's position in alphabet for list positionning
    currentRowNumber = string.lowercase.index(grafanaData['target'].lower())
    # If list is empty then user clicked on this field before buuilding a query
    if not global_allRow_availableCurvesList[currentRowNumber] :
        return jsonify(['ERROR : User did not build any query'])
    if len(global_allRow_availableCurvesList[currentRowNumber]) == 1 and global_allRow_availableCurvesList[currentRowNumber][0] != 'NO DATA POINT' :
        return jsonify(['ERROR : User picked wrong differenciation option'])
    else :
        return jsonify(global_allRow_availableCurvesList[currentRowNumber])


#########################################################################################################################
##                                                                                                                     ##
##                 RETRIEVING GRAFANA'S JSON && SENDING TO RIVERBED && SENDING RIVERBED RESPONSE                       ##
##                                                                                                                     ##
#########################################################################################################################
@serverFlask.route("/query", methods = ['POST'])
def query():
    ########################################## First part : collect raw data ###########################################
                            ##################################################################
                            ##                 Gathering Grafana's data                     ##
                            ##################################################################
    # This global variable contains the last report, filters will be manually applied on   
    global globalAllCurves
    global globalReadableDeviceDict
    global global_allRow_deviceID
    global global_allRow_availableCurvesList
    global global_allRow_readableMetricDict
    global global_allRow_differenciationOptionsList
    global_allRow_availableCurvesList = [0]*26
    rollup = False
    
    differenciationSelected = ''
    curveSelected = ''

    # List returned to Grafana
    dataPointsForGrafana = []
    # Catch the JSON sent by Grafana (current route /query is the only one receiving JSON from Grafana (check onChangeInternal())
    grafanaFieldsForQuery = request.get_json()
    # For each row of Grafana query (A, B, C, D...)
    for currentTarget in grafanaFieldsForQuery['targets']:
        
        # RefId is identification for one row in Grafana (A, B, C ...) automaticly created by Grafana
        grafanaRefId = currentTarget['refId']
        grafanaRefIdNumber = string.lowercase.index(grafanaRefId.lower())
        
        # Variable for listing interfaces belonging to device (endpoint /getInterfaces)
        deviceID = currentTarget['deviceID']

        # print('Current row : '+grafanaRefId+' | number : '+str(string.lowercase.index(grafanaRefId.lower())))
        global_allRow_deviceID[string.lowercase.index(grafanaRefId.lower())] = deviceID
        global_allRow_metricClassID[string.lowercase.index(grafanaRefId.lower())] = currentTarget['metricClassID']

        # Retrieving metric queried by Grafana (default is '')
        metricClassID = currentTarget['metricClassID']
        metricID = currentTarget['metricID']
        localMetricID = currentTarget['metricID']
        sourceType = currentTarget['type']
        if sourceType == 'Device':
            objectType = 'DEVICE'
            objectId = currentTarget['deviceID']
        if sourceType == 'Interface':
            objectType = 'INTERFACE'
            objectId = currentTarget['interfaceID']

        # If all informations needed to construct query are not ready, go back to loop start
        if objectType == 'Interface' and objectId == '':
            continue
        if  objectId == '' or metricID =='' or metricClassID == '':
            continue
        
        # Retrieving times queried from Grafana's JSON (string epoch format needed)
        queryTimeMillisecFrom = str(convert_to_epoch(grafanaFieldsForQuery['range']['from'])*1000)
        queryTimeMillisecTo = str(convert_to_epoch(grafanaFieldsForQuery['range']['to'])*1000)


                            ##################################################################
                            ##                    Building NetIM query                      ##
                            ##################################################################
        dataDefs = {
                    'startTime': queryTimeMillisecFrom,
                    'endTime': queryTimeMillisecTo,
                    'metricClassId': metricClassID,
                    'metricId':[metricID],
                    'objectType': objectType,
                    'objectId': [objectId]
        }

        # print(json.dumps(dataDefs, indent=4, sort_keys=True))

        # Converting data_defs in JSON, JSON format is required by Riverbed SteelCentral NetIM server
        dataDefsJSON = json.dumps(dataDefs)
        
        # Query is now ready to be sent to Riverbed SteelCentral NetIM
        # API for reports creation
        urlReportCreation = basicHttpAuth+'/v1/metric-data'
        # Sending datadefs to Riverbed SteelCentral NetIM and waiting for response
        reportFromNetIM = requestData(urlReportCreation, dataDefsJSON)

        # print('\n\n\n###### BEGIN : JSON BUILT BY GRAFANA #######')
        # print(json.dumps(grafanaFieldsForQuery, indent=4, sort_keys=True))
        # print('###### END : JSON BUILT BY GRAFANA #######\n\n\n')
        
                            ##################################################################
                            ##                     Gathering NetIM's data                   ##
                            ##################################################################
        # Response is parsed in order to access some fields
        parsedReport = json.loads(reportFromNetIM.text)

        # print('\n\n\n###### DEBUT NETIM JSON #######')
        # print(json.dumps(reportFromNetIM.json(), indent=4, sort_keys=True))
        # print('###### FIN NETIM JSON #######\n\n\n')

        # WORKING BUT NO MORE DIFFERENCE BETWEEN VALUE=0 AND NO VALUE
        # Get it off for debug purpose
        try:
            parsedReport["items"][0]['samples']
        except LookupError as e:
            global_allRow_availableCurvesList[grafanaRefIdNumber] = ['NO DATA POINT']
            global_allRow_differenciationOptionsList[grafanaRefIdNumber]  = ['NO DATA POINT']
            continue

        # allSamplesFromNetim is a list containing summary data from Riverbed AppResponse probe
        allSamplesFromNetim = parsedReport["items"][0]['samples']['items']

        # Check if NetIM returned only a couple (timestamp, metric)
        # If triplet or more, constructing variable allMetricsPresentInNetimReport that contains each metrics different of timestamp and metric called in box 'Metric'
        # to let user select the correct metric
        
        allMetricsPresentInNetimReport = []
        otherMetricThanTimestamp ='' 
        for currentSample in allSamplesFromNetim:       
            checkCouple = 0
            rollup = currentSample['rollup']
            # Depending on metric queried, NetIM can return a lot of fields as metrics (CPUindex, className....) 
            # Collecting them in order to use them as filter later
            for metricReturnedByNetIM in currentSample['values'] :
                checkCouple = checkCouple + 1
                if metricReturnedByNetIM != 'timestamp' :
                    # Variable used in case of couple, to draw graph automatically (without differentiation)
                    otherMetricThanTimestamp = metricReturnedByNetIM
                if metricReturnedByNetIM not in allMetricsPresentInNetimReport :
                    allMetricsPresentInNetimReport.append(metricReturnedByNetIM)

        # Construction differenciation list with both name and id
        if currentTarget['differenciation'] == "" :
            global_allRow_differenciationOptionsList[grafanaRefIdNumber] = []
            del global_allRow_differenciationOptionsList[grafanaRefIdNumber][:]
            # For each line of global_allRow_readableMetricDict (global_allRow_readableMetricDict = ALL {metricName : metricId})
            for eachLine in allMetricsPresentInNetimReport:
                # Check if metric is in the good metric from metricClass list, not timestamp nor metricID
                if eachLine in global_allRow_readableMetricDict[grafanaRefIdNumber] and metricID != eachLine and eachLine != 'timestamp':
                    global_allRow_differenciationOptionsList[grafanaRefIdNumber].append({'text': str(global_allRow_readableMetricDict[grafanaRefIdNumber][eachLine]), 'value':str(eachLine)})


                            ##################################################################
                            ##                        Single curve case                     ##
                            ##################################################################
        # If only only a couple (timestamp, metric) is spotted, show the graph
        if checkCouple == 2 :
            # If no result, skip to new loop
            try:
                parsedReport["items"][0]['samples']
            except KeyError as e:
                continue

            datapoints = {"disabled":[],"aggregateavgrollup":[],"aggregateminrollup":[],"aggregatemaxrollup":[]}
            rollupSelected = currentTarget['rollupType']

            if rollup == False :
                for value in allSamplesFromNetim:
                
                    timeStampMilliSecInteger= (int(value['values']['timestamp']))
                    if value['values'][otherMetricThanTimestamp] == '' :
                        res = 0
                    else :
                        res = float(value['values'][otherMetricThanTimestamp])
                    # Adding couple [value, timestamp] to datapoints list
                    datapoints['disabled'].append([res,timeStampMilliSecInteger])
                # Var caption contains curve's caption (id : mectric)
                caption = deviceID+' : '+otherMetricThanTimestamp
                # Object representating each row's of Grafana (contains caption, meta informations, row's id, collection time, and datapoints)
                newTarget = {
                    # target is curve's caption
                    "target" : caption,
                    # meta is miscellaneous informations
                    "meta" :   { 'info 1' : "nothing"},
                    # refId is the letter of the row (A, B, C, D ...)
                    'refId' :  grafanaRefId,
                    # datapoints is a list containing all points retrieved by Riverbed AppResponse probe
                    "datapoints" : datapoints[rollupSelected]    
                    }
                # Each target (or row) is insert into a list (will be send to Grafana)
                dataPointsForGrafana.append(newTarget)
                global_allRow_availableCurvesList[grafanaRefIdNumber] = ['Request is full : single curve query']
                global_allRow_differenciationOptionsList[grafanaRefIdNumber] = ['Request is full : single curve query']
                # No need to go deeper in loop
                rollup = False
                continue

            if rollup == True :
                for value in allSamplesFromNetim:
                    timeStampMilliSecInteger= (int(value['rollupTimestamp']))
                    if value['values'][otherMetricThanTimestamp] == '' :
                        res = 0
                    else :
                        res = float(value['values'][otherMetricThanTimestamp])
                    print(json.dumps(value, indent=4, sort_keys=True))
                    rollupReading = value['rollupAlgo']
                    if value['values']['timestamp'] == '':
                        continue
                    # Adding couple [value, timestamp] to datapoints list
                    datapoints[rollupReading].append([res,timeStampMilliSecInteger])
            # Var caption contains curve's caption (id : mectric)
            caption = deviceID+' : '+otherMetricThanTimestamp
            # Object representating each row's of Grafana (contains caption, meta informations, row's id, collection time, and datapoints)
            newTarget = {
                # target is curve's caption
                "target" : caption,
                # meta is miscellaneous informations
                "meta" :   { 'info 1' : "nothing"},
                # refId is the letter of the row (A, B, C, D ...)
                'refId' :  grafanaRefId,
                # datapoints is a list containing all points retrieved by Riverbed AppResponse probe
                "datapoints" : datapoints[rollupSelected]    
                }
            # Each target (or row) is insert into a list (will be send to Grafana)
            dataPointsForGrafana.append(newTarget)
            global_allRow_availableCurvesList[grafanaRefIdNumber] = ['Request is full : single curve query']
            global_allRow_differenciationOptionsList[grafanaRefIdNumber] = ['Request is full : single curve query']
            # No need to go deeper in loop
            rollup = False
            continue

                            ##################################################################
                            ##                        Multi curves case                     ##
                            ##################################################################
        if currentTarget['differenciation'] != "" :
            # If user has already choose the differenciation, we create all curves avalaible for this differenciation
            differenciationSelected = currentTarget['differenciation']  
            if rollup == False :
                # Datapoint is a list which will receive all datapoints in correct format [value, timestamp]
                # May be deleted
                datapoints = []

                # Dict (will receive all curves from query)
                globalAllCurves = {}
                # Hard reset current curve list
                global_allRow_availableCurvesList[grafanaRefIdNumber] = []
                del global_allRow_availableCurvesList[grafanaRefIdNumber][:]
                # Var for curve name checking
                nameDiff = ''
                # For each sample
                for currentSample in allSamplesFromNetim:
                    # Retrieve timestamp (for whatever reason, empty timestamp can occur)
                    if currentSample['values']['timestamp'] == '' :
                        continue
                    
                    timeStampMilliSecInteger= (int(currentSample['values']['timestamp']))
                    # Checking differenciated field's name (can be INP-D1, INP-D2 ...)
                    nameDiff = currentSample['values'][differenciationSelected]
                    # If this one has not already been met, adding it to avalaible curves list and initialize as empty list
                    if nameDiff not in global_allRow_availableCurvesList[grafanaRefIdNumber] :
                        global_allRow_availableCurvesList[grafanaRefIdNumber].append(nameDiff)
                        globalAllCurves.update({nameDiff:[]})
                    # If empty value, use 0 
                    if currentSample['values'][localMetricID] == '' :
                        res = 0
                    # Else, value is set to float
                    else :
                        res = float(currentSample['values'][localMetricID])
                    # adding couple timestamp value to the curve
                    globalAllCurves[nameDiff].append([res,timeStampMilliSecInteger])
            
            if rollup == True :
                rollupSelected = currentTarget['rollupType']
                # Datapoint is a list which will receive all datapoints in correct format [value, timestamp]
                # May be deleted
                datapoints = []
                # Dict (will receive all curves from query)
                globalAllCurves = {}
                # Hard reset current curve list
                global_allRow_availableCurvesList[grafanaRefIdNumber] = []
                del global_allRow_availableCurvesList[grafanaRefIdNumber][:]
                # Var for curve name checking
                nameDiff = ''
                # For each sample
                for currentSample in allSamplesFromNetim:
                    # Retrieve timestamp (for whatever reason, empty timestamp can occur)
                    if currentSample['values']['timestamp'] == '' :
                        continue
                    
                    timeStampMilliSecInteger= (int(currentSample['values']['timestamp']))
                    # Checking differenciated field's name (can be INP-D1, INP-D2 ...)
                    nameDiff = currentSample['values'][differenciationSelected]
                    # If this one has not already been met, adding it to avalaible curves list and initialize as empty list
                    if nameDiff not in global_allRow_availableCurvesList[grafanaRefIdNumber] :
                        global_allRow_availableCurvesList[grafanaRefIdNumber].append(nameDiff)
                        globalAllCurves.update({nameDiff:{"disabled":[],"aggregateavgrollup":[],"aggregateminrollup":[],"aggregatemaxrollup":[]}})
                    # If empty value, use 0 
                    if currentSample['values'][localMetricID] == '' :
                        res = 0
                    # Else, value is set to float
                    else :
                        res = float(currentSample['values'][localMetricID])
                    # adding couple timestamp value to the curve
                    globalAllCurves[nameDiff][currentSample['rollupAlgo']].append([res,timeStampMilliSecInteger])

            curveSelected = currentTarget['selectedCurve']
            if curveSelected != '' :
                if rollup == False :
                    # Full caption (device accessName : metric)
                    if deviceID in globalReadableDeviceDict :
                        deviceName = globalReadableDeviceDict[deviceID]
                    else :
                        deviceName = 'deviceSelected'

                    # Var caption contains curve's caption (id : mectric)
                    caption = deviceName+' : '+otherMetricThanTimestamp +' '+differenciationSelected+' ' + curveSelected
                    # Object representating each row's of Grafana (contains caption, meta informations, row's id, and datapoints)

                    try:
                        parsedReport["items"][0]['samples']
                        newTarget = {
                                # target is curve's caption
                                "target": caption,
                                # meta is miscellaneous informations
                                "meta" :   { 'info 1' : "nothing"},
                                # refId is the letter of the row (A, B, C, D ...)
                                'refId' :  grafanaRefId,
                                # datapoints is a list containing all points retrieved by Riverbed NetIM probe
                                "datapoints": globalAllCurves[curveSelected]    
                                }
                    except KeyError as e:
                        continue
                    # Each target (or row) is insert into a list (will be send to Grafana)
                    dataPointsForGrafana.append(newTarget)
                if rollup == True :
                    # Full caption (device accessName : metric)
                    if deviceID in globalReadableDeviceDict :
                        deviceName = globalReadableDeviceDict[deviceID]
                    else :
                        deviceName = 'deviceSelected'

                    # Var caption contains curve's caption (id : mectric)
                    caption = deviceName+' : '+otherMetricThanTimestamp +' '+differenciationSelected+' ' + curveSelected
                    # Object representating each row's of Grafana (contains caption, meta informations, row's id, and datapoints)

                    try:
                        parsedReport["items"][0]['samples']
                        newTarget = {
                                # target is curve's caption
                                "target": caption,
                                # meta is miscellaneous informations
                                "meta" :   { 'info 1' : "nothing"},
                                # refId is the letter of the row (A, B, C, D ...)
                                'refId' :  grafanaRefId,
                                # datapoints is a list containing all points retrieved by Riverbed NetIM probe
                                "datapoints": globalAllCurves[curveSelected][rollupSelected]    
                                }
                    except KeyError as e:
                        continue
                    # Each target (or row) is insert into a list (will be send to Grafana)
                    dataPointsForGrafana.append(newTarget)
    
    rollup = False
    # Finaly, sending data to Grafana in JSON format        
    return jsonify(dataPointsForGrafana) 
            

# Server started, accepts external connection on port 0000, debug set to false in oreder to avoid security issue
if (__name__ == "__main__"):
    serverFlask.run(host = '0.0.0.0', port = 0000, debug=False)