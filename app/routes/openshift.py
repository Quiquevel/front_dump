from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, validator
from functions.dyna import getenvironmentsclusterslist, dynatracetreatment

pod_delete = APIRouter(tags=["v1"])
alerting_status = APIRouter(tags=["v1"])

environmentList = getenvironmentsclusterslist("spain")

class pod_2_delete(BaseModel):
    functional_environment: str
    cluster: str
    region: str
    namespace: str
    pod: list

    @validator("functionalEnvironment")
    def validate_environment(cls, v):
        if not any(x in v for x in ["dev","pre","pro"]):
            raise HTTPException(status_code=400, detail=f"{v} value is not valid for functionalEnvironment")
        return v
    
    #To validate the cluster parameter.
    @validator("cluster")
    def validate_cluster(cls, v):
        if not any(x in v for x in ["ohe","bks","probks","dmzbbks","dmzbazure","ocp05azure","ohe","probks","dmzbbks","azure","prodarwin","dmzbdarwin","proohe","dmzbohe","confluent"]):
            raise HTTPException(status_code=400, detail=f"{v} value is not valid for cluster")
        return v
    
    @validator("namespace")
    def validate_namespace(cls,v):
        return v
    
    #to validate the region parameter
    @validator("region")
    def validate_region(cls, v):
        if not any(x in v for x in ["bo1","bo2","weu1","weu2"]):
            raise HTTPException(status_code=400, detail=f"{v} value is not valid for region")
        return v

class check_token(BaseModel):
    ldap: str

class DynaModel(BaseModel):
    functional_environment: str
    timedyna: str = None
 
    @validator("functionalEnvironment")
    def validate_environment(cls, v):        
        if not any(x == v for x in environmentList):
            raise HTTPException(status_code = 400, detail=f"{v} value is not valid for functionalEnvironment")
        return v
    
@alerting_status.post("/dynatrace", tags = ["v1"], description = "GET DYNATRACE ALERT", response_description = "JSON", status_code = 200)
async def get_dynatrace_alert(target: DynaModel):
    return await dynatracetreatment(functional_environment = target.functional_environment, timedyna = target.timedyna)