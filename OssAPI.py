#其中把文件上传到oss中，返回下载的url
import oss2
import SysConfig
import util
from oss2.credentials import EnvironmentVariableCredentialsProvider
from oss2.models import OSS_TRAFFIC_LIMIT



def upload_and_get_signed_url(mp3_filename):
    # Your OSS endpoint and bucket information
    endpoint =SysConfig.oss_endpoint
    _accessKeyId = SysConfig.oss_accessKeyId
    _accessKeySecret = SysConfig.oss_accessKeySecret
    bucket_name = SysConfig.oss_bucket_name

    # Authentication
    auth = oss2.Auth(_accessKeyId, _accessKeySecret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    # The object key in the bucket and local file path are the same as mp3_filename
    key = mp3_filename
    local_audio_file_path = mp3_filename

    # Upload the audio file
    with open(local_audio_file_path, 'rb') as fileobj:
        bucket.put_object(key, fileobj)

    # Set download speed limit (e.g., 10000 KB/s)
    limit_speed = (10000 * 1024 * 8)
    params = {OSS_TRAFFIC_LIMIT: str(limit_speed)}

    # Create a signed URL for limited speed download, with an expiry time of 5000 seconds
    url = bucket.sign_url('GET', key, 5000, params=params)

    return url



def upload_and_get_signed_key(mp4_filename):


    # Your OSS endpoint and bucket information
    endpoint = SysConfig.oss_endpoint
    _accessKeyId = SysConfig.oss_accessKeyId
    _accessKeySecret = SysConfig.oss_accessKeySecret
    bucket_name = SysConfig.oss_bucket_name

    # Authentication
    auth = oss2.Auth(_accessKeyId, _accessKeySecret)
    bucket = oss2.Bucket(auth, endpoint, bucket_name)

    # The object key in the bucket and local file path are the same as mp3_filename
    
    key = util.generate_osskey(util.getFileName(mp4_filename))
    local_audio_file_path = mp4_filename

    # Upload the audio file
    with open(local_audio_file_path, 'rb') as fileobj:
        bucket.put_object(key, fileobj)

    # Set download speed limit (e.g., 10000 KB/s)
    limit_speed = (10000 * 1024 * 8)
    params = {OSS_TRAFFIC_LIMIT: str(limit_speed)}

    # Create a signed URL for limited speed download, with an expiry time of 5000 seconds
    url = bucket.sign_url('GET', key, 5000, params=params)

    return key,url
