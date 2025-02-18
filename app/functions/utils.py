import requests, json, urllib3, datetime, time
import streamlit as st

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

url = "https://santander.pro.dynatrace.cloudcenter.corp/e/a9b631ff-5285-454a-9b3e-4355527a91fd/api/v1"

def get_date():
  now = datetime.datetime.now()
  return now.strftime("%Y%m%d_%H%M")

def fetch_problems(url, token):
    request_url = url + "/v2/problems"
    headers = {"Authorization": "Api-Token " + token, "Accept": "application/json; charset=utf-8"}
    params = {"problemSelector": "status(\"open\")"}
    res = requests.get(request_url, headers=headers, verify=False, params=params)
    return res.json()["problems"]

def extract_problem_details(problem):
    r_numero = "NC"
    r_proyecto = "NC"
    r_pod = "NC"
    r_region = "NC"

    if problem["title"] in ["Long garbage-collection time", "Memory resources exhausted"]:
        for tag in problem["entityTags"]:
            if tag["key"] == "PROYECTO_PaaS2.0":
                r_proyecto = tag["value"]
                r_numero = problem["displayId"]
            elif tag["key"] == "Region_test":
                r_region = tag["value"]
            elif tag["key"] == "task":
                r_pod = tag["value"]

    return r_numero, r_proyecto, r_pod, r_region

def print_problem_details(problems):
    for problem in problems:
        r_numero, r_proyecto, r_pod, r_region = extract_problem_details(problem)
        if r_region != "NC":
            print(f'{r_numero:5} --> {r_proyecto:40}/ {r_pod:55} --> {r_region}')

def get_gc():
    global TOKEN_1, url
    problems = fetch_problems(url, TOKEN_1)
    print_problem_details(problems)
    
APPLICATION_JSON = "application/json"
BEARER_PREFIX = "Bearer "

def tokenparameter(env=None, cluster=None,region=None,do_api=None,namespace=None,microservice=None,pod=None, delete=False, idtoken=False, ldap=False):
    #DEV URL API
    #urlapi  = "https://shuttle-openshift-heapdump-sanes-shuttlepython-dev.apps.san01bks.san.dev.bo1.paas.cloudcenter.corp"
    #PRO URL API
    urlapi = "https://shuttle-openshift-heapdump-sanes-shuttle-pro.apps.san01darwin.san.pro.bo1.paas.cloudcenter.corp"

    match do_api:
        case 'namespacelist':
            request_url = f"{urlapi}/dumps/namespace_list"
            headers = {"Accept": APPLICATION_JSON,"Authorization":BEARER_PREFIX+str(idtoken),"x-clientid":"darwin"}
            body = {
                "functionalenvironment": env,
                "cluster": cluster,
                "region": region,
                "ldap" : ldap
            }
            response = requests.post(url=request_url,headers=headers,data=json.dumps(body), verify=False,timeout=120)
            if response.status_code == 200:
                datos = response.text
                json_object = json.loads(datos)
                return json_object
            else:
                st.write(f"Error: {response.status_code} - {response.text}")

        case 'microservicelist':
            request_url = f"{urlapi}/dumps/microservices_list"
            headers = {"Accept": APPLICATION_JSON,"Authorization":BEARER_PREFIX+str(idtoken),"x-clientid":"darwin"}
            body = {
            "functionalenvironment": env,
            "cluster": cluster,
            "region": region,
            "namespace": namespace,
            "ldap" : ldap
            }
            response = requests.post(url=request_url,headers=headers,data=json.dumps(body), verify=False,timeout=120)
            if response.status_code == 200:
                datos = response.text
                json_object = json.loads(datos)
                return json_object
            else:
                st.write(f"Error: {response.status_code} - {response.text}")
                
        case 'podlist':
            request_url = f"{urlapi}/dumps/pod_list"
            headers = {"Accept": APPLICATION_JSON,"Authorization":BEARER_PREFIX+str(idtoken),"x-clientid":"darwin"}
            body = {
            "functionalenvironment": env,
            "cluster": cluster,
            "region": region,
            "namespace": namespace,
            "microservices": microservice,
            "ldap" : ldap
            }
            response = requests.post(url=request_url,headers=headers,data=json.dumps(body), verify=False,timeout=120)
            if response.status_code == 200:
                datos = response.text
                json_object = json.loads(datos)
                return json_object
            else:
                st.write(f"Error: {response.status_code} - {response.text}")

        case "heapdump":
            request_url = f"{urlapi}/dumps/heapdump"
            headers = {"Accept": APPLICATION_JSON,"Authorization":BEARER_PREFIX+str(idtoken),"x-clientid":"darwin"}
            body = {
                "functionalenvironment": env,
                "cluster": cluster,
                "region": region,
                "namespace": namespace,
                "pod": [pod],
                "action": "1",
                "delete": delete,
                "ldap": ldap
                }
            response = requests.post(url=request_url,headers=headers,data=json.dumps(body), verify=False,timeout=200)
            if response.status_code == 200:
                return response.content
            else:
                json_object = [{"heapdump": None}]
                return json_object
            
        case "heapdump_datagrid":
            request_url = f"{urlapi}/dumps/heapdump"
            headers = {"Accept": APPLICATION_JSON,"Authorization":BEARER_PREFIX+str(idtoken),"x-clientid":"darwin"}
            body = {
                "functionalenvironment": env,
                "cluster": cluster,
                "region": region,
                "namespace": namespace,
                "pod": [pod],
                "action": "3",
                "delete": delete,
                "ldap": ldap
                }
            response = requests.post(url=request_url,headers=headers,data=json.dumps(body), verify=False,timeout=200)
            if response.status_code == 200:
                return response.content
            else:
                json_object = [{"heapdumpdatagrid": None}]
                return json_object
            
        case "threaddump":
            request_url = f"{urlapi}/dumps/heapdump"
            headers = {"Accept": APPLICATION_JSON,"Authorization":BEARER_PREFIX+str(idtoken),"x-clientid":"darwin"}
            body = {
                "functionalenvironment": env,
                "cluster": cluster,
                "region": region,
                "namespace": namespace,
                "pod": [pod],
                "action": "2",
                "delete": delete,
                "ldap": ldap
                }
            response = requests.post(url=request_url,headers=headers,data=json.dumps(body), verify=False,timeout=120)
            if response.status_code == 200:
                return response.content
            else:
                json_object = [{"threaddump": None}]
                return json_object
            
        case "threaddump_datagrid":
            request_url = f"{urlapi}/dumps/heapdump"
            headers = {"Accept": APPLICATION_JSON,"Authorization":BEARER_PREFIX+str(idtoken),"x-clientid":"darwin"}
            body = {
                "functionalenvironment": env,
                "cluster": cluster,
                "region": region,
                "namespace": namespace,
                "pod": [pod],
                "action": "4",
                "delete": delete,
                "ldap": ldap
                }
            response = requests.post(url=request_url,headers=headers,data=json.dumps(body), verify=False,timeout=120)
            if response.status_code == 200:
                return response.content
            else:
                json_object = [{"threaddumpdatagrid": None}]
                return json_object

def get_jvm_dump(optionenv, optioncluster, optionregion, selectnamespace, selectpod, type, delete, idtoken, ldap):
    progress_text = "⏳ Operation in progress. Please wait."
    my_bar = st.progress(0, text=progress_text)
    file_content = tokenparameter(env=optionenv, cluster=optioncluster, region=optionregion, namespace=selectnamespace, pod=selectpod, do_api=type, delete=delete, idtoken=idtoken, ldap=ldap)
    for percent_complete in range(100):
        time.sleep(0.1)
        my_bar.progress(percent_complete + 1, text=progress_text)    
    st.success('Done!')

    date = get_date()
    if file_content != [{type: None}]:
        st.download_button(
            label="Download dump file 🔽",
            data=file_content,
            file_name=f'{type}-{selectpod}-{date}.gz',
            mime='application/octet-stream',
        )
    else:
        st.warning("Error generating dump. The selected pod has not the neccesary tools for generating dumps. Please contact Domain.")

def execute_dump(optionenv, optioncluster, optionregion, namespace, pod, delete, idtoken, ldap, do_execute=None):
    dump_types = {
        "HeapDump": "heapdump",
        "HeapDump DataGrid": "heapdump_datagrid",
        "ThreadDump": "threaddump",
        "ThreadDump DataGrid": "threaddump_datagrid"
    }

    if do_execute in dump_types:
        execute_button = st.button('Execute')
        if execute_button:
            try:
                get_jvm_dump(optionenv, optioncluster, optionregion, namespace, pod, dump_types[do_execute], delete, idtoken, ldap)
            except Exception as e:
                st.write(f'Error downloading file: {e}')

if __name__ == '__main__':
	TOKEN_1 = 'oBSioZKCTXi0-bwwtTftN'
	get_gc()