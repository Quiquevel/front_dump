# shuttle-openshift-front-dump
## Indications for deploying in different environments:

DEV:  
In the file /app/functions/utils.py, modify the following lines in the "tokenparameter" function so that they look like this:  
    #DEV URL API  
    urlapi  = "https://shuttle-openshift-heapdump-sanes-shuttlepython-dev.apps.san01bks.san.dev.bo1.paas.cloudcenter.corp"  
    #PRO URL API  
    #urlapi = "https://shuttle-openshift-heapdump-sanes-shuttlepython-pro.apps.san01darwin.san.pro.bo1.paas.cloudcenter.corp"  

PRO:  
In the file /app/functions/utils.py, modify the following lines in the "tokenparameter" function so that they look like this:  
    #DEV URL API  
    #urlapi  = "https://shuttle-openshift-heapdump-sanes-shuttlepython-dev.apps.san01bks.san.dev.bo1.paas.cloudcenter.corp"  
    #PRO URL API  
    urlapi = "https://shuttle-openshift-heapdump-sanes-shuttlepython-pro.apps.san01darwin.san.pro.bo1.paas.cloudcenter.corp"  
