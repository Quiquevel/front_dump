from shuttlelib.openshift.client import OpenshiftClient
from shuttlelib.utils.logger import logger
from urllib3 import disable_warnings, exceptions
from functions.switch import getswitchstatus
from pytz import timezone
from datetime import datetime, timedelta
from sys import platform
import os, aiohttp

disable_warnings(exceptions.InsecureRequestWarning)

LGC = "Long garbage-collection time"
MRE = "Memory resources exhausted"

dynavariables = {
    "onpremise": {
        "urlbaseproblem": os.getenv("DYNA_URI_BASEPROBLEM_ESP"),
        "urlbaseapi": os.getenv("DYNA_URI_BASEAPI_ESP"),        
        "managementZone": os.getenv("DYNA_MANAGEMENTZONE_ESP"),
        "token": os.getenv("TOKEN_DYNA_ESP"),
        "proxy": None
    },
    "saas": {
        "urlbaseproblem": os.getenv("DYNA_URI_BASEPROBLEM_SaaS"),
        "urlbaseapi": os.getenv("DYNA_URI_BASEAPI_SaaS"),
        "managementZone": os.getenv("DYNA_MANAGEMENTZONE_SaaS"),
        "token": os.getenv("TOKEN_DYNA_SaaS"),
        "proxy": os.getenv("PROXY_DYNA_SaaS")
    }
}

dynavariableskeys = ["onpremise", "saas"]
for key in dynavariableskeys:
    dynavariables[key]["urlbasepagesize"] = (
        (dynavariables[key]["urlbaseapi"] or "") + "?nextPageKey="
    )
    if dynavariables[key]["token"] is not None:
        dynavariables[key]["headers"] = {
            "Authorization": "Api-Token " + dynavariables[key]["token"],
            "Accept": "application/json; charset=utf-8"
            }
    else:
        dynavariables[key]["headers"] = {
            "Authorization": "Api-Token ",
            "Accept": "application/json; charset=utf-8"
            }
 
def getenvironmentsclusterslist(entityid):
    client = OpenshiftClient(entityid=entityid)
    environmentlist = []    
    clusternamelist = []
    clusterurllist = []
    
    environmentlist = list(client.clusters.keys())
    for environment in environmentlist:
        clusternamelist = list(client.clusters[environment])
        for cluster in clusternamelist:
            if 'azure' in cluster:
                clusterurl = client.clusters[environment][cluster]['weu1']['url']
                clusterurllist.append(clusterurl)
            else: 
                clusterurl = client.clusters[environment][cluster]['bo1']['url']
                clusterurllist.append(clusterurl)

    environmentlist.extend([x.upper() for x in environmentlist])    
    clusternamelist.extend([x.upper() for x in clusternamelist])
    clusternamelist = list(set(clusternamelist))
    clusternamelist.sort()
    
    return environmentlist, clusternamelist

async def dynatracetreatment(functionalenvironment, timedyna = None):
    logger.info("starting getDynaProblems process")
    
    switchednamespaces = await getswitchstatus(functionalenvironment)
    detailalertlist = await getdynaproblems(timedyna, switchednamespaces)
    
    logger.info("finished getDynaProblems process")

    return detailalertlist

async def getdynaproblems(timedyna, switchednamespaces):
    detailalertlist = []
    detailalertlistcurrent = []
    detailalertlistnext = []
    nextpagekey = ""
    
    global urlbaseproblem
    global urlbaseapi
    global headers
    global proxy

    if timedyna == None:
        timedyna = "now"

    async with aiohttp.ClientSession() as session:
        for key in dynavariableskeys:            
            headers = dynavariables[key]["headers"]
            params = {"from":timedyna, "problemSelector":dynavariables[key]["managementZone"], "pageSize":"500"}
            urlbaseapi = dynavariables[key]["urlbaseapi"]
            urlbasepagesize = dynavariables[key]["urlbasepagesize"]
            urlbaseproblem = dynavariables[key]["urlbaseproblem"]
            proxy = dynavariables[key]["proxy"]
            
            try:
                logger.info(f"Dynatrace GetProblems {key}")
                logger.info(f"Dynatrace GetProblems Proxy: {proxy}")
                async with session.get(urlbaseapi, headers = headers, params = params, ssl = False, proxy = proxy) as res:
                    res_json = await res.json()
                    ps = res_json['problems']

            except aiohttp.client_exceptions.ServerTimeoutError:
                logger.error(f"Timeout detected against {urlbaseapi} ")
                infodetailalert = {'alertingType': None, 'problemId': None, 'urlproblem': None, 'snowId': None, 'urlsnow': None, 'incidentProvider': 'Dynatrace', 'status': None, 'start': None, 'end': None, 'namespace': None, 'microservice': None, 'cluster': None, 'region': None, 'switchStatus': None} 
                detailalertlist.append(infodetailalert)
                return detailalertlist
            except aiohttp.client_exceptions.ClientError as e:
                logger.error(f"{urlbaseapi} could not be retrieved. Skipping...")
                infodetailalert = {'alertingType': None, 'problemId': None, 'urlproblem': None, 'snowId': None, 'urlsnow': None, 'incidentProvider': 'Dynatrace', 'status': None, 'start': None, 'end': None, 'namespace': None, 'microservice': None, 'cluster': None, 'region': None, 'switchStatus': None}
                detailalertlist.append(infodetailalert)
                return detailalertlist
            except Exception as e:
                logger.error(f"An unexpected error occurred: {e}")
                infodetailalert = {'alertingType': None, 'problemId': None, 'urlproblem': None, 'snowId': None, 'urlsnow': None, 'incidentProvider': 'Dynatrace', 'status': None, 'start': None, 'end': None, 'namespace': None, 'microservice': None, 'cluster': None, 'region': None, 'switchStatus': None}
                detailalertlist.append(infodetailalert)
                return detailalertlist

            detailalertlistcurrent = await loopdynaproblems(ps, switchednamespaces)
            detailalertlist.extend(detailalertlistcurrent)
            try:
                nextpagekey = res_json['nextPageKey']
            except KeyError:
                nextpagekey = None            
            while nextpagekey is not None:
                async with session.get(urlbasepagesize + nextpagekey, headers = headers, ssl = False, proxy = proxy) as resnextpagekey:
                    resnextpagekey_json = await resnextpagekey.json()
                    try:
                        nextpagekey = resnextpagekey_json['nextPageKey']
                    except KeyError:
                        nextpagekey = None
                    psnext = resnextpagekey_json['problems']
                    detailalertlistnext = await loopdynaproblems(psnext, switchednamespaces)
                    detailalertlist.extend(detailalertlistnext)

            logger.info(f"Dynatrace alerts getDynaProblems (after {key} execution Total: {len(detailalertlist)})")
        logger.info(f"Dynatrace alerts getDynaProblems (Total: {len(detailalertlist)})")
    return detailalertlist

async def loopdynaproblems(ps, switchednamespaces):
    detailalertlist = []
    alerttypelist = [LGC, MRE]
    
    global hostdetectedlist
    global namespace
    global microservice
    global platform

    for p in range(len(ps)):
        paasproblem = ps[p]
        problemtags = paasproblem["entityTags"]        
        dates,datee = await matchproblemtime(paasproblem["startTime"], paasproblem["endTime"])
        displayid = paasproblem["displayId"]
        problemid = paasproblem["problemId"]
        title = paasproblem["title"]
        status = paasproblem["status"]
        
        if displayid == "P-240817741":
            logger.info(f"Skipping problem with display ID: {displayid}")
            continue

        if paasproblem["title"] in alerttypelist and len(problemtags) > 0:
            for t in range(len(problemtags)):
                value = problemtags[t].get("value", None)
                key = problemtags[t]['key']

                if value:              
                    await matchproblemtags(key, value)

            if not namespace:
                try:
                    namespaceaux = paasproblem['affectedEntities'][0]['name']            
                except KeyError:
                    pass

                if "-pro" in namespaceaux:
                    namespaceaux = namespaceaux.split("-")
                    x = slice(3)
                    namespaceaux = namespaceaux[x]
                    namespaceaux = '-'.join(namespaceaux)
                    namespace = namespaceaux
                else:
                    try:
                        managementzones = paasproblem['managementZones']
                    except KeyError:
                        pass
                    for t in range(len(managementzones)):
                        managementzone = managementzones[t]
                        if "-pro" in managementzone['name']:
                            namespaceaux = managementzone['name']
                            namespaceaux = namespaceaux.split("- ")
                            namespace = ''.join(namespaceaux[-1:])
                            break

            detailalert = await paasproblemreport(displayid, problemid, title, status, dates, datee, namespace, microservice, platform, hostdetectedlist, switchednamespaces)

            platform = None
            namespace= None
            microservice = None
            hostdetectedlist = None

            if len(detailalert) != 0:
                detailalertlist.extend(detailalert)
            hostdetectedlist = []
        
    return detailalertlist

async def matchproblemtime(starttime, endtime):
    datee = None

    summer = await is_summer(datetime.today())
    if summer:
        delta = 0
    else:
        delta = 1
     
    datedyna = int(starttime)/1000
    dates = datetime.fromtimestamp(datedyna)
    dates = dates + timedelta(hours = delta)
    dates = dates.strftime('%Y-%m-%d %H:%M:%S')

    if int(endtime) != -1:
        datedyna = int(endtime)/1000
        datee = datetime.fromtimestamp(datedyna)
        datee = datee + timedelta(hours = delta)
        datee = datee.strftime('%Y-%m-%d %H:%M:%S')

    return (dates, datee)

hostdetectedlist = []
async def matchproblemtags(key, value):
    global platform
    global namespace
    global microservice
    global hostdetectedlist

    match key:
        case "HostDetectedName":            
            hostdetected = value
            hostdetectedlist.append(hostdetected)            
        case "PLATFORM":
            platform = value
        case "PROYECTO_PaaS2.0":
            namespace = value
        case "Container_name":
            microservice = value            
        case "Microservicio":
            microservice = value

async def paasproblemreport(displayid, problemid, type, status, start, end, namespace, microservice, platform, hostdetectedlist, switchednamespaces):
    detailalertlist = []

    #find switchednamespaces
    switched = [x for x in switchednamespaces if x == namespace]
    if switched:
        switchstatus = True
    else:
        switchstatus = False

    match type:
        case 'Long garbage-collection time':
            detailalertlist = await detailalertfill(type, problemid, displayid, status, start, end, namespace, microservice, platform, hostdetectedlist, switchstatus)
        case 'Memory resources exhausted':
            detailalertlist = await detailalertfill(type, problemid, displayid, status, start, end, namespace, microservice, platform, hostdetectedlist, switchstatus)
        case 'Response time degradation':            
            detailalertlist = await detailalertfill(type, problemid, displayid, status, start, end, namespace, microservice, platform, hostdetectedlist, switchstatus)
        case 'Failure rate increase':            
            detailalertlist = await detailalertfill(type, problemid, displayid, status, start, end, namespace, microservice, platform, hostdetectedlist, switchstatus)
        case "Multiple service problems":            
            detailalertlist = await detailalertfill(type, problemid, displayid, status, start, end, namespace, microservice, platform, hostdetectedlist, switchstatus)
        case _:
            logger.warning(f"Unhandled alert type: {type}")
            detailalertlist = []

    return detailalertlist

async def is_summer(dt):
    tz = timezone("Europe/Madrid")
    aware_dt = tz.localize(dt)
    
    return aware_dt.dst() != timedelta(0,0)

async def detailalertfill(type, problemid, displayid, status, start, end, namespace, microservice, platform, hostdetectedlist, switchstatus):    
    detailalertlist = []
    
    global urlbaseproblem
    global urlbaseapi

    urlproblem = urlbaseproblem + problemid
    inforegion = await paasproblemregion(hostdetectedlist)      
    platform = await paasproblemplatform(platform, hostdetectedlist) 
    idsnow, urlsnow = await matchproblemsnow(problemid)
    
    if not platform and (type == MRE or type == LGC):
        platform = await matchhostname(problemid, urlbaseapi)
        
    if inforegion != None:
        validateregion = inforegion.split(", ")
        if validateregion:
            for region in validateregion:
                infodetailalert = {
                    'alertingType': type,
                    'problemId': displayid,
                    'urlproblem': urlproblem,
                    'snowId': idsnow,
                    'urlsnow': urlsnow,
                    'incidentProvider': 'Dynatrace',
                    'status': status,
                    'start': start,
                    'end': end,
                    'namespace': namespace,
                    'microservice': microservice,
                    'cluster': platform,
                    'region': region,
                    'switchStatus': switchstatus
                } 
                detailalertlist.append(infodetailalert)
    else:        
        infodetailalert = {
            'alertingType': type,
            'problemId': displayid,
            'urlproblem': urlproblem,
            'snowId': idsnow,
            'urlsnow': urlsnow,
            'incidentProvider': 'Dynatrace',
            'status': status,
            'start': start,
            'end': end,
            'namespace': namespace,
            'microservice': microservice,
            'cluster': platform,
            'region': None,
            'switchStatus': switchstatus
        } 
        detailalertlist.append(infodetailalert)

    return detailalertlist

async def paasproblemregion(hostdetectedlist):
    if len(hostdetectedlist) == 0:
        return None

    for hostnames in hostdetectedlist:        
        try:
            hostname = hostnames.split(", ")
            region= set()
            hostnames = [nodo.split(".")[4] for nodo in hostname if "." in nodo]            
            if len(hostnames) > 0:
                region.update(hostnames)
                region= ", ".join(str(item) for item in region)
            else:
                region = None
        except IndexError:
            region = None
    
    return region

async def paasproblemplatform(cluster, hostdetectedlist):
    hostname_to_platform = {
        "san01.san.dmzb": "dmzbohe",
        "san01darwin.san.pro": "prodarwin",
        "san01darwin.san.dmzb": "dmzbdarwin",
        "san01confluent.san": "confluent",
        "san01bks.san.pro": "probks",
        "san01bks.san.dmzb": "dmzbbks",
        "san01mov.san.dmz2b": "dmz2bmov",
        "ocp05.san.pro": "azure",
        "weu": "azure"
    }
    
    if len(hostdetectedlist) == 0:
        platform = None
        return platform        

    if cluster == "AZURE" or cluster == "AZURE_CCC":
        platform = "azure"
        return platform    
    else:
        for hostname in hostdetectedlist:
            for key, platform in hostname_to_platform.items():
                if key in hostname:
                    return platform
        return None
                 
async def matchproblemsnow(problemid):
    idsnow = None
    urlsnow = None
    
    global urlbaseapi
    global headers
    global proxy
    
    params = None
    urlrequestproblem = urlbaseapi + '/' + problemid

    async with aiohttp.ClientSession() as session:
        try:            
            async with session.get(urlrequestproblem, headers=headers, params=params, ssl=False, proxy=proxy) as res:
                ps = await res.json()
                logger.info(f"Dynatrace response: {res.status}, {res.reason}")
        except aiohttp.client_exceptions.ServerTimeoutError:
            logger.error(f"Timeout detected against {urlrequestproblem} ")            
            return None, None
        except aiohttp.client_exceptions.ClientError as e:
            logger.error(f"{urlrequestproblem} could not be retrieved due to client error: {e}. Skipping...")                        
            return None, None

        try:
            comments = ps["recentComments"]                
        except KeyError:
            return None, None
        
        for comment in comments['comments']:
            if comment['content'].startswith("Incidencia creada en ServiceNow"):
                datos = comment['content'].split("\n")
                try:
                    urlsnow = datos[3] 
                except IndexError:
                    return None, None
                idsnow = datos[0].split(":")
                idsnow = str(idsnow[1].strip())

    return idsnow, urlsnow


async def matchhostname(problemid, urlbaseapi = None):
    params = None
    urlrequestproblem = urlbaseapi + '/' + problemid

    async with aiohttp.ClientSession() as session:
        try:            
            async with session.get(urlrequestproblem, headers=headers, params=params, ssl=False, proxy=proxy) as res:
                ps = await res.json()
        except aiohttp.client_exceptions.ServerTimeoutError:
            logger.error(f"Timeout detected against {urlrequestproblem} ")            
            return None
        except aiohttp.client_exceptions.ClientError as e:
            logger.error(f"{urlrequestproblem} could not be retrieved due to client error: {e}. Skipping...")                        
            return None
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return None

        try:
            evidencedetails = ps['evidenceDetails']['details']
        except KeyError:
            logger.error("KeyError: 'evidenceDetails' or 'details' not found in response")
            return None

        for t in range(len(evidencedetails)):
            evidence = evidencedetails[t]
            if evidence['evidenceType'] == 'EVENT':
                properties = evidence['data']['properties']

                if evidence['displayName'] == MRE:
                    for t in range(len(properties)):                    
                        key = properties[t]['key']                   
                        if key == 'host.name':
                            host = properties[t].get("value", None)
                            platform = await paasproblemplatform(None, [host])
                            return platform                        
                elif evidence['displayName'] == LGC:
                    for t in range(len(properties)):                    
                        key = properties[t]['key']