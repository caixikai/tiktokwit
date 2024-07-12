import threading
import json
import time
import SysConfig

from volcengine.base.Service import Service
from volcengine.ServiceInfo import ServiceInfo
from volcengine.Credentials import Credentials
from volcengine.ApiInfo import ApiInfo

class SAMIService(Service):
    _instance_lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        if not hasattr(SAMIService, "_instance"):
            with SAMIService._instance_lock:
                if not hasattr(SAMIService, "_instance"):
                    SAMIService._instance = object.__new__(cls)
        return SAMIService._instance

    def __init__(self):
        self.service_info = SAMIService.get_service_info()
        self.api_info = SAMIService.get_api_info()
        super(SAMIService, self).__init__(self.service_info, self.api_info)

    @staticmethod
    def get_service_info():
        api_url = 'open.volcengineapi.com'
        
        service_info = ServiceInfo(api_url, {}, Credentials('', '', 'sami', 'cn-north-1'), 10, 10,scheme='http')
        #def __init__(self, host, header, credentials, connection_timeout, socket_timeout, scheme='http'):

        return service_info

    @staticmethod
    def get_api_info():
        api_info = {
            "GetToken": ApiInfo("POST", "/", {"Action": "GetToken", "Version": "2021-07-27"}, {}, {}),
        }
        return api_info

    def common_json_handler(self, api, body):
        params = dict()
        try:
            body = json.dumps(body)
            res = self.json(api, params, body)
            res_json = json.loads(res)
            return res_json
        except Exception as e:
            res = str(e)
            try:
                res_json = json.loads(res)
                return res_json
            except:
                raise Exception(str(e))




def volcengine_get_Token():

    AUTH_VERSION = "2021-07-27"
    tokenVersion = "volc-auth-v1"

    Region = "cn-north-1"
    Host = 'open.volcengineapi.com'
    ContentType = "application/x-www-form-urlencoded"

    # 请求的凭证，从IAM或者STS服务中获取

    ACCESS_KEY = SysConfig.volcengine_sami_access_key
    SECRET_KEY = SysConfig.volcengine_sami_secret_key
    appKey = SysConfig.volcengine_sami_appKey

    sami_service = SAMIService()
    sami_service.set_ak(ACCESS_KEY)
    sami_service.set_sk(SECRET_KEY)
    
    req = {
        "appkey": appKey,
        "token_version": tokenVersion,
        "expiration": 3600
    }
    
    for attempt in range(3):

        try:
            resp = sami_service.common_json_handler("GetToken", req)
            print("response task_id=%s status_code=%d status_text=%s expires_at=%s\n\t token=%s" % (
                resp["task_id"], resp["status_code"], resp["status_text"], resp["expires_at"], resp["token"]
            ))

            return resp["token"]
        except Exception as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            time.sleep(61)
            print("sleep 61s")
            if attempt == 2:  # If it's the last attempt, raise the exception
                print("get token failed, ", resp)
            else:
                print("Retrying...")           




if __name__ == '__main__':
    token =volcengine_get_Token()
    print(token)