import streamlit as st
from functions.utils import tokenparameter, execute_dump
from streamlit_javascript import st_javascript
from functions.dyna import getdynaproblems, getswitchstatus

def update_selected_problem():
    st.session_state.update({"selected_problem": st.session_state.problem_selectbox})

async def do_dump_project():
    idtoken = st_javascript("localStorage.getItem('idToken');")
    ldap = st_javascript("localStorage.getItem('ldap');")
    
    if not idtoken or not ldap:
        st.error("Failed to retrieve idToken or ldap from localStorage.")
        return

    st.title('🚨 JAVA Dump 🚨')
    
    optioncluster = None
    optionregion = None
    SELECT_PROBLEM = "Select a problem..."
    
    #Integration test with DYNA
    timedyna = "now-30m"
    switchednamespaces = await getswitchstatus(optioncluster)
    st.markdown("## Dynatrace Open Problems")

    # Initialize session state variables if not present
    if 'show_problems' not in st.session_state:
        st.session_state.show_problems = False
    if 'problems' not in st.session_state:
        st.session_state.problems = []
    if 'selected_problem' not in st.session_state:
        st.session_state.selected_problem = SELECT_PROBLEM

    # Button to load problems
    if st.button("Opened Problem's Pods in Dynatrace"):
        st.session_state.show_problems = True
        st.session_state.problems = await getdynaproblems(timedyna=timedyna, switchednamespaces=switchednamespaces)
    
    # Display problems if loaded
    if st.session_state.show_problems:
        problems = st.session_state.problems
        
        if problems:
            problems.insert(0, SELECT_PROBLEM)
            selected_problem = st.selectbox(
                "Select an open problem", 
                problems, 
                index=problems.index(st.session_state.selected_problem) if st.session_state.selected_problem in problems else 0,
                key="problem_selectbox",
                on_change=update_selected_problem
            )

            # Verify that a valid problem is selected
            if st.session_state.selected_problem != SELECT_PROBLEM:
                st.write(f"Selected Problem: {st.session_state.selected_problem}")

                # Extract information for selected problem
                env_problem = 'pro'
                cluster_problem = st.session_state.selected_problem['cluster']
                region_problem = st.session_state.selected_problem['region']
                namespace_problem = st.session_state.selected_problem['namespace']
                microservice_problem = st.session_state.selected_problem['microservice']
                
                json_object_pod = tokenparameter(
                    env=env_problem, cluster=cluster_problem, region=region_problem,
                    namespace=namespace_problem, microservice=microservice_problem,
                    do_api='podlist', idtoken=idtoken, ldap=ldap
                )
                
                if json_object_pod is not None:
                    flat_pod = [x for x in json_object_pod]
                    selectpod = st.selectbox('Select Pod', ([''] + flat_pod), key="pod_selectbox")
                    
                    if selectpod != '':
                        selectedheap = st.selectbox('Select type', ('', 'HeapDump', 'ThreadDump', 'HeapDump DataGrid', 'ThreadDump DataGrid'), key="opt_restart_r")
                        execute_dump(
                            optionenv=env_problem, optioncluster=cluster_problem, optionregion=region_problem,
                            namespace=namespace_problem, pod=selectpod, delete=False,
                            idtoken=idtoken, ldap=ldap, do_execute=selectedheap
                        )
            else:
                st.write("No problem selected.")
        else:
            st.write("No open problems found.")

    # Display environment, cluster, and region selection
    delete = st.checkbox('Delete pod after dump?')
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        optionenv = st.selectbox('Select Environment', ('pro', 'pre', 'dev'), key="optionenv")

    col1, col2, col3 = st.columns(3)
    SELECT_CLUSTER = 'Select Cluster'
    with col1:
        match optionenv:
            case 'pro':
                optioncluster = st.selectbox(SELECT_CLUSTER, ('', 'prodarwin', 'dmzbdarwin', 'azure', 'confluent', 'dmz2bmov', 'probks', 'dmzbbks', 'dmzbazure', 'ocp05azure'), key="optioncluster1")
            case 'pre':
                optioncluster = st.selectbox(SELECT_CLUSTER, ('', 'azure', 'bks', 'ocp05azure'), key="optioncluster1")
            case 'dev':
                optioncluster = st.selectbox(SELECT_CLUSTER, ('', 'azure', 'bks', 'ocp05azure'), key="optioncluster1")

    SELECT_REGION = 'Select Region'
    with col2:
        match optionenv:
            case 'dev':
                if 'azure' in optioncluster:
                    optionregion = st.selectbox(SELECT_REGION, ('', 'weu1'), key="optioncluster2")
                else:
                    optionregion = st.selectbox(SELECT_REGION, ('', 'bo1'), key="optioncluster3")
            case _:
                if optioncluster in ['azure', 'dmzbazure', 'ocp05azure']:
                    optionregion = st.selectbox(SELECT_REGION, ('', 'weu1', 'weu2'), key="optioncluster2")
                else:
                    optionregion = st.selectbox(SELECT_REGION, ('', 'bo1', 'bo2'), key="optioncluster3")

    with col3:
        if optioncluster and optionregion:
            json_object_namespace = tokenparameter(
                env=optionenv, cluster=optioncluster, region=optionregion,
                do_api='namespacelist', idtoken=idtoken, ldap=ldap
            )
            if json_object_namespace:
                flat_list = [x for x in json_object_namespace]
                selectnamespace = st.selectbox('Select Namespace', ([''] + flat_list), key="selectnamespace1")
                
                if selectnamespace:
                    json_object_microservice = tokenparameter(
                        env=optionenv, cluster=optioncluster, region=optionregion,
                        namespace=selectnamespace, do_api='microservicelist', idtoken=idtoken, ldap=ldap
                    )
                    if json_object_microservice:
                        flat_micro = [x for x in json_object_microservice]
                        selectmicroservice = st.selectbox('Select Microservice', ([''] + flat_micro), key="selectmicroservice1")
                        
                        if selectmicroservice:
                            json_object_pod = tokenparameter(
                                env=optionenv, cluster=optioncluster, region=optionregion,
                                namespace=selectnamespace, microservice=selectmicroservice,
                                do_api='podlist', idtoken=idtoken, ldap=ldap
                            )
                            if json_object_pod:
                                flat_pod = [x for x in json_object_pod]
                                selectpod = st.selectbox('Select Pod', ([''] + flat_pod), key="pod1")
                                
                                if selectpod:
                                    selectedheap = st.selectbox('Select type', ('', 'HeapDump', 'ThreadDump', 'HeapDump DataGrid', 'ThreadDump DataGrid'), key="opt_restart_r")
                                    execute_dump(
                                        optionenv=optionenv, optioncluster=optioncluster, optionregion=optionregion,
                                        namespace=selectnamespace, pod=selectpod, delete=delete,
                                        idtoken=idtoken, ldap=ldap, do_execute=selectedheap
                                    )
    st.text('')
    st.text('')
    st.link_button("Help for analysis", "https://sanes.atlassian.net/wiki/x/oABatAU", help="Go to documentation with tools and help to do the analysis")
    return delete