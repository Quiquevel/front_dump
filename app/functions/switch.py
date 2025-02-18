from shuttlelib.utils.logger import logger
import aiohttp, os

async def getswitchstatus(functional_environment):
    if functional_environment == 'pro':
        logger.debug("Get namespaces with Switch = True")
        url = os.getenv("SWITCH_API_URI")
        path = os.getenv("SWITCH_API_PATH")
        request_url = url + path
        headers = {"Accept": "application/json"}
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(request_url, headers=headers, ssl=False) as answer:
                    switchedanswer = await answer.json()
                    logger.debug(f"Response: {answer.status}, {answer.reason}")
                    if answer.status == 200:
                        resultswitch = list(set([ r["namespace"] for r in switchedanswer if r["switch"] == True ]))
                        logger.debug(f"answer switch 'True': {resultswitch}")
                        return resultswitch
                    else:
                        resultswitch = ['no-switch']
                        logger.debug(f"answer: {resultswitch}")
                        return resultswitch
        except aiohttp.client_exceptions.ServerTimeoutError:
            logger.error(f"Timeout detected against {request_url} ")
            resultswitch = ['no-switch']
            return resultswitch
        except Exception:
            logger.error(f"{request_url} could not be retrieved. Skipping...")
            resultswitch = ['no-switch']
            return resultswitch
    else:
        resultswitch = ['no-switch']
        logger.debug(f"Answer: {resultswitch}")
        return resultswitch