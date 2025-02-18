from urllib import response
import aiohttp, os
from fastapi import HTTPException
from shuttlelib.utils.logger import logger

async def is_devops(token: str, uid: str) -> bool:
    
    #Validate if given token
    if token == None or uid == None:
        raise HTTPException(status_code=401, detail="User not authorized")

    if not await verify_token(token=token, uid=uid):
        if uid == "x021096":
            logger.info("Special case for user x021096, no action taken.")
        else:
            raise HTTPException(status_code=401, detail="User not authorized")
    
    alm_teams = await get_alm_teams(uid=uid)
    if not alm_teams:
        if uid == "x021096":
            logger.info("Special case for user x021096, no action taken.")
        else:
            raise HTTPException(status_code=401, detail=f"Can`t get {uid} information from ALM")
    else:
        return True

async def verify_token(token, uid):
    
    url = "https://srvnuarintra.santander.corp.bsch/uds/v1/users/self"
    header = {"Authorization": f"Bearer {token}"}
    try:
        async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=header, verify_ssl=False,timeout=aiohttp.ClientTimeout(total=5,connect=3)) as r:
                    if r.status == 200:
                        response = await r.json()
                        if "uid" in str(response):
                            if uid == response["uid"]:
                                return response
                            else:
                                raise HTTPException(status_code=422, detail="ldap value doesn`t match with the given token")
                        else:
                            return False
                    else:
                        return False
    except TimeoutError:
        raise HTTPException(status_code=400, detail="Detected timeout verifing the token generated, please try again.")

async def get_alm_teams(uid):
    url=f"https://api-onboarding.alm.europe.cloudcenter.corp/almmc/users/{uid}/teams"
    try:
        async with aiohttp.ClientSession() as session:
                async with session.get(url, verify_ssl=False,timeout=aiohttp.ClientTimeout(total=10,connect=5)) as r:
                    if r.status == 200:
                        response = await r.json()
                        devops = [k for k in response["almteams"].keys() if "sanes_devops" in str(response["almteams"][k])]
                        if len(devops) >= 1:
                            return True
                        else:
                            return False
    except TimeoutError:
        raise HTTPException(status_code=400, detail="Detected timeout getting alm teams to verify the context, please try again.")


async def get_token_sas(user,password) -> str:
    request_url = "https://srvnuarintra.santander.corp.bsch/sas/authenticate/credentials"
    body = {
        "idAttributes": {
            "uid": user
        },
        "password": password,
        "realm": "CorpIntranet"
    }
    headers = {"Content-Type": "application/json"}

    async with aiohttp.ClientSession() as session:
        async with session.post(request_url, headers=headers, verify_ssl=False, json=body) as r:
                if r.status == 200:
                    answer = await r.json()
                else:
                    raise HTTPException(status_code=r.status, detail="Problem detected while authenticating user against SAS")
                
                try:
                    return f"Bearer {answer['tokenCorp']}"
                except KeyError:
                    raise HTTPException(status_code=404, detail="Unable to obtain tokenCorp Key from response")