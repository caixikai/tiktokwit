# coding:utf-8
from __future__ import print_function
import os
import time
import json
import retrying
import SysConfig

from Logger import SystemLogger
from VideoAPI import retry
from util import combine_path_and_filename

from volcengine.vod.VodService import VodService
from volcengine.vod.models.request.request_vod_pb2 import VodUrlUploadRequest
from volcengine.vod.models.request.request_vod_pb2 import VodQueryUploadTaskInfoRequest
from volcengine.imp.ImpService import ImpService
from volcengine.imp.models.request.request_imp_pb2 import ImpSubmitJobRequest
from volcengine.imp.models.request.request_imp_pb2 import ImpRetrieveJobRequest
from volcengine.vod.models.request.request_vod_pb2 import VodGetMediaInfosRequest
from volcengine.vod.models.request.request_vod_pb2 import VodUpdateMediaPublishStatusRequest
from volcengine.vod.models.request.request_vod_pb2 import VodGetPlayInfoRequest



def upload_video(url):
    # 配置VOD服务
    vod_service = VodService()


    # 设置AK和SK
    vod_service.set_ak(SysConfig.volcengine_upload_AK)
    vod_service.set_sk(SysConfig.volcengine_upload_SK)

    # 空间名称
    space_name = 'space-guukp0'

    try:
        # 创建上传请求
        req = VodUrlUploadRequest()
        req.SpaceName = space_name
        url_set = req.URLSets.add()
        url_set.SourceUrl = url
        url_set.FileExtension = '.mp4'
        url_set.CallbackArgs = ''
        
        # 发送上传请求
        resp = vod_service.upload_media_by_url(req)
        # 处理响应
        if resp.ResponseMetadata.Error.Code == '':
            print("Upload successful")
            print("Job ID:", resp.Result.Data[0].JobId)
            print("Source URL:", resp.Result.Data[0].SourceUrl)
            return resp.Result.Data[0].JobId
        else:
            print("Error:", resp.ResponseMetadata.Error)
            print("Request ID:", resp.ResponseMetadata.RequestId)
            return None
    except Exception as e:
        print("An error occurred:", str(e))
        return None
    



def poll_upload_task_status(job_id):
    vod_service = VodService()

    # 设置AK和SK
    vod_service.set_ak(SysConfig.volcengine_upload_AK)
    vod_service.set_sk(SysConfig.volcengine_upload_SK)

    req = VodQueryUploadTaskInfoRequest()
    req.JobIds = job_id

    while True:
        try:
            resp = vod_service.query_upload_task_info(req)
            if resp.ResponseMetadata.Error.Code == '':
                # 检查任务的状态
                media_info_list = resp.Result.Data.MediaInfoList
                if media_info_list:
                    state = media_info_list[0].State
                    print("Current state:", state)
                    if state == 'success':  # 检查完成状态，根据实际状态调整
                        print("Task completed successfully.")
                        Vid = media_info_list[0].Vid
                        print("Current Vid:", Vid)
                        return Vid
                    elif state == 'failed':  # 检查完成状态，根据实际状态调整
                        return 0
                else:
                    print("No media info available yet.")
            else:
                print("Error:", resp.ResponseMetadata.Error)
                print("Request ID:", resp.ResponseMetadata.RequestId)
                break
        except Exception as e:
            print("An error occurred:", str(e))
            break
        
        time.sleep(3)  # 暂停3秒后再次轮询




def submit_imp_job(space_name, file_id, template_id, callback_args):
    """
    Submits a job to the IMP service with specified parameters.

    Args:
    space_name (str): Space name in VOD.
    file_id (str): File ID of the video in VOD.
    template_id (str): Template ID for processing the video.
    callback_args (str): Callback arguments.

    Returns:
    The response from the IMP service or an error message.
    """

    imp_service = ImpService()
    imp_service.set_ak(SysConfig.volcengine_upload_AK)
    imp_service.set_sk(SysConfig.volcengine_upload_SK)

    try:
        req = ImpSubmitJobRequest()
        req.InputPath.Type = 'VOD'  # 素材库：VODMaterial 视频库：VOD
        req.InputPath.VodSpaceName = space_name
        req.InputPath.FileId = file_id
        req.TemplateId = template_id
        req.CallbackArgs = callback_args
        resp = imp_service.submit_job(req)
    except Exception as e:
        return f"An error occurred: {str(e)}"
    else:
        print("Response:\n", resp)
        if resp.ResponseMetadata.Error.Code == '':
            return resp.Result
        else:
            return resp.ResponseMetadata.Error

# coding:utf-8

import json

@retry(attempts=3, delay=5, error_message="查询清除字幕task失败")
def epoll_job_statusV1_retry(job_ids):
    return poll_job_statusV1(job_ids)


def poll_job_statusV1(job_ids):
    """
    Periodically polls the job status every 3 seconds.

    Args:
        job_ids (list): List of Job IDs to poll.
    """
    imp_service = ImpService()
    # Set the access key and secret key
    imp_service.set_ak(SysConfig.volcengine_upload_AK)
    imp_service.set_sk(SysConfig.volcengine_upload_SK)

    req = ImpRetrieveJobRequest()
    req.JobIds.extend(job_ids)

    all_jobs_completed = True
    job_details = []

    while True:
        try:
            resp = imp_service.retrieve_job(req)
            if resp.ResponseMetadata.Error.Code == '':
                #print("Response:\n", resp)
                print("Result:\n", resp.Result)
                print(type(resp.Result))
                # Check if the job is complete or not
                # Assuming 'COMPLETE' is the state we are checking for
                for job_id, job_info in resp.Result.items():
                    print("Job ID:", job_id)
                    job_status = job_info.Status
                    print("Job Status:", job_status)


                    if (job_status != 'Completed' and job_status != 'Failed'):
                        all_jobs_completed = False
                        continue
                    else:
                        # Assume job_info has Outputs if job is completed
                        outputs = job_info.Output
                        for output in outputs:
                            if (output.Status == 'Completed'):
                                # Extract details like file IDs if available
                                if hasattr(output, 'Properties'):
                                    if output.Properties != '':
                                        properties_json = json.loads(output.Properties)
                                        file_ids = properties_json.get('OutputPath', {}).get('FileIds', [])

                                        if len(file_ids) !=0 :
                                            job_details.append({
                                                        'job_id': job_id,
                                                        'file_ids': file_ids,
                                                        'job_status':output.Status 
                                                    })
                            elif ( output.Status == 'Failed'):
                                   job_details.append({
                                                        'job_id': job_id,
                                                        'file_ids': [],
                                                        'job_status':output.Status 
                                                    })

                        return job_details
            else:
                print("Error:\n", resp.ResponseMetadata.Error)
                break
        except Exception as e:
            print("An error occurred:", str(e))
            break

        time.sleep(3)  # Wait for 3 seconds before polling again






def get_media_infos(vids):
    """
    Retrieves media information for given video IDs and returns their publish status.

    Args:
        vids (list): List of video IDs to retrieve info for.
        ak (str): Access Key for VolcEngine API.
        sk (str): Secret Key for VolcEngine API.

    Returns:
        dict: A dictionary with video IDs as keys and their publish statuses as values.
    """
    vod_service = VodService()
    vod_service.set_ak(SysConfig.volcengine_upload_AK)
    vod_service.set_sk(SysConfig.volcengine_upload_SK)

    try:
        req = VodGetMediaInfosRequest()
        req.Vids = vids
        resp = vod_service.get_media_infos(req)
        if resp.ResponseMetadata.Error.Code == '':
            publish_statuses = {}
            for media_info in resp.Result.MediaInfoList:
                '''
                vid = media_info.BasicInfo.Vid
                publish_status = media_info.BasicInfo.PublishStatus
                publish_statuses[vid] = publish_status
                '''
                print("Media info retrieved successfully.")
                # 将JSON字符串解析为字典
 
                return media_info
  
        else:
            print("Error:", resp.ResponseMetadata.Error)
            return None
    except Exception as e:
        print("An exception occurred:", str(e))
        return None



def update_media_publish_status(vid, status):
    """
    Updates the publish status of a media identified by the video ID.

    Args:
        vid (str): Video ID of the media to update.
        status (str): New publish status to set for the media.
        ak (str): Access Key for VolcEngine API.
        sk (str): Secret Key for VolcEngine API.

    Returns:
        str: Success message or error message.
    """
    vod_service = VodService()
    vod_service.set_ak(SysConfig.volcengine_upload_AK)
    vod_service.set_sk(SysConfig.volcengine_upload_SK)

    try:
        req = VodUpdateMediaPublishStatusRequest()
        req.Vid = vid
        req.Status = status
        resp = vod_service.update_media_publish_status(req)
        if resp.ResponseMetadata.Error.Code == '':
            return 'Update media publish status success'
        else:
            return f"Error: {resp.ResponseMetadata.Error}"
    except Exception as e:
        return f"An exception occurred: {str(e)}"





def get_play_info(vid, ssl='0', need_original='1', union_info=None):
    """
    Retrieves play information for a given video ID from Volcengine VOD Service.

    Args:
        vid (str): Video ID for which to retrieve play info.
        ssl (str): Whether the play URL needs to be SSL encrypted ('1' for true).
        need_original (str): Whether the original file info is needed ('1' for true).
        union_info (str, optional): Additional information for union scenarios.
        ak (str, optional): Access Key for VolcEngine API.
        sk (str, optional): Secret Key for VolcEngine API.

    Returns:
        str: The main play URL or an error message.
    """
    vod_service = VodService()

    vod_service.set_ak(SysConfig.volcengine_upload_AK)
    vod_service.set_sk(SysConfig.volcengine_upload_SK)

    try:
        req = VodGetPlayInfoRequest()
        req.Vid = vid
        req.Ssl = ssl
        req.NeedOriginal = need_original
        if union_info:
            req.UnionInfo = union_info
        resp = vod_service.get_play_info(req)
        if resp.ResponseMetadata.Error.Code == '':
            return resp.Result.PlayInfoList[0].MainPlayUrl
        else:
            return f"Error: {resp.ResponseMetadata.Error}"
    except Exception as e:
        return f"An exception occurred: {str(e)}"
    

import requests

from datetime import datetime

@retry(attempts=3, delay=5, error_message="下载文件失败")
def download_with_retry(url):
    local_filename = None
    try:
        local_filename = download_video(url)
        if local_filename:
            print(f"下载后本地视频的文件名: {local_filename}")
            return local_filename
    except Exception as e:
        print(f"下载失败: {e}")
        raise
    finally:
        if not local_filename:
            raise Exception("下载失败，文件名为 None")


def download_video_V0(url):
    local_filename = url.split('/')[-1]
    session = requests.Session()
    try:
        with session.get(url, stream=True, timeout=(10, 60)) as r:
            r.raise_for_status()
            with open(local_filename, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
        return local_filename
    except requests.exceptions.RequestException as e:
        print(f"下载时出错: {e}")
        raise
    finally:
        session.close()


def download_video_v1(url):
    """
    Downloads a video from a given URL, saves it to a local path with a filename based on the current timestamp, and returns the save path.

    Args:
        url (str): URL of the video to download.

    Returns:
        str: The path where the video was saved, or None if there was an error.
    """
    # Generate a filename based on the current datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # Year, month, day, hour, minute, second, microsecond
    current_file_path = os.path.abspath(__file__)
   
    save_path = f"{timestamp}.mp4"  # Save as an MP4 file
    save_path= combine_path_and_filename(current_file_path,save_path)

    try:
        response = requests.get(url, stream=True)
        if response.status_code == 200:
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:  # filter out keep-alive new chunks
                        f.write(chunk)
            print(f"Video downloaded successfully: {save_path}")
            return save_path  # Return the path to the saved video file
        else:
            print(f"Failed to download video. Status code: {response.status_code}")
            return None
    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {url}: {str(e)}")
        return None


def clear_video_subtitles(video_url):
   
    #从阿里云通过URL批量上传文件
    job_id = upload_video(video_url)
    print("用过URL上传文件到火山引擎的JobID:", job_id)
    #查询视频是否上传成功
    file_id = poll_upload_task_status(job_id)
    print("上传文件到火山引擎的Job返回的FileId:",file_id)

    #提交擦除视频的task
    space_name = 'space-guukp0'
    #file_id = 'v0263dg10004coi9hggfcpirnp759fdg'
    template_id = '0322d8c082494a64a636ac24afbec5d9'
    callback_args = ''
    taskId = submit_imp_job(space_name, file_id, template_id, callback_args)
    print("提交擦除视频的taskId:", taskId)
   
    #taskId="9c42262ba183ef118555d920dc220578"
    #查询
    job_ids = [taskId]
    queryJobs_Result= epoll_job_statusV1_retry(job_ids)
    SystemLogger.info(f'提交擦除视频的task返回的结果:{queryJobs_Result}')
    
    for result in queryJobs_Result:
        job_id = result['job_id']
        file_ids = result['file_ids']
        #job_status =result['job_status']
        job_status=result['job_status']
        
        for file_id in file_ids:
            media_info = get_media_infos(file_id)  
            print(f"Media info for job {job_id}, file {file_id}: {media_info} jobstatus:{job_status}")
            
            if (media_info.BasicInfo.PublishStatus == "Unpublished"):
                SystemLogger.info(f"文件 {file_id} 是未发布状态")
                vid = file_id
                status = 'Published'
                SystemLogger.info(f"文件 {file_id} 更新成发布状态")
                result = update_media_publish_status(vid, status)
                #改成发布状态后，查询一下下载的地址
                MainPlayUrl=  get_play_info(file_id)
                SystemLogger.info(f"发布后视频下载的URL:{MainPlayUrl}")
                #local_filename = download_video(MainPlayUrl)
                try:
                    local_filename= download_with_retry(MainPlayUrl)
                except Exception as e:
                    SystemLogger.info("下载失败:", e)

                print(f"下载后本地视频的文件名:{local_filename}")
                return local_filename,job_status
                #return local_filename,'Failed'
                


            elif(media_info.BasicInfo.PublishStatus == "Published"):

                SystemLogger.info(f"文件 {file_id} 是发布状态.")
                MainPlayUrl=  get_play_info(file_id)
                SystemLogger.info(f"发布后视频下载的URL:{MainPlayUrl}")

                try:
                    local_filename= download_with_retry(MainPlayUrl)
                except Exception as e:
                    SystemLogger.info("下载失败:", e)

                SystemLogger.info(f"下载后本地视频的文件名:{local_filename}")
                return local_filename,job_status
    return None,"Failed"

def combine_path_and_filename(path, filename):
    return os.path.join(os.path.dirname(path), filename)

@retry(attempts=3, delay=5, error_message="下载文件失败")
def download_video(url):
    """
    Downloads a video from a given URL, saves it to a local path with a filename based on the current timestamp, and returns the save path.

    Args:
        url (str): URL of the video to download.

    Returns:
        str: The path where the video was saved, or None if there was an error.
    """
    # Generate a filename based on the current datetime
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S%f")  # Year, month, day, hour, minute, second, microsecond
    current_file_path = os.path.abspath(__file__)
    save_path = f"{timestamp}.mp4"  # Save as an MP4 file
    save_path = combine_path_and_filename(current_file_path, save_path)

    session = requests.Session()
    try:
        response = session.get(url, stream=True, timeout=(10, 60))
        response.raise_for_status()
        with open(save_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:  # filter out keep-alive new chunks
                    f.write(chunk)
        print(f"Video downloaded successfully: {save_path}")
        return save_path  # Return the path to the saved video file
    except requests.exceptions.RequestException as e:
        print(f"Error during requests to {url}: {str(e)}")
        if os.path.exists(save_path):
            os.remove(save_path)
        return None
    finally:
        session.close()

if __name__ == '__main__':


    '''
    video_url = 'https://smartboximagesavecxk.oss-cn-shenzhen.aliyuncs.com/images/20240421100149175_0420.mp4?Expires=1716285713&OSSAccessKeyId=LTAI5tBBouBKye2QVf8Fop65&Signature=FC8cnrVx0UnLKG5I8DxImL7XEnk%3D'
    languagename ="德文"
    

 # Record the overall start time
    overall_start = datetime.now()
    print(f"Process started at {overall_start}================================")

    # Subtitle clearing step
    start_clear_subtitle = datetime.now()
    print(f"Starting clear subtitle at {start_clear_subtitle}================================")
    video_path = clear_video_subtitles(video_url)
    end_clear_subtitle = datetime.now()
    duration_clear_subtitle = end_clear_subtitle - start_clear_subtitle
    print(f"Finished clear subtitle at {end_clear_subtitle}================================")
    print(f"Duration for clearing subtitles: {duration_clear_subtitle}")

    # Translation step
    start_translation = datetime.now()
    print(f"Starting translation to {languagename} at {start_translation}================================")
    translatevideoV3(video_path, languagename)
    end_translation = datetime.now()
    duration_translation = end_translation - start_translation
    print(f"Finished translation to {languagename} at {end_translation}================================")
    print(f"Duration for translation to {languagename}: {duration_translation}")

    # Record the overall end time and calculate the total duration
    overall_end = datetime.now()
    total_duration = overall_end - overall_start
    print(f"Process ended at {overall_end}================================")
    print(f"Total duration for the process: {total_duration}")
    '''
    '''
    #从阿里云通过URL批量上传文件
    video_url="https://smartboximagesavecxk.oss-cn-shenzhen.aliyuncs.com/images/20240506140915280_20240502135543813461_soraapi_20240502134631.mp4"
    SystemLogger.info(f'开始推送OSS文件到火山:{video_url}' )
    job_id = upload_video(video_url)
    SystemLogger.info(f'用过URL上传文件到火山引擎的JobID:{job_id}' )
    #查询视频是否上传成功
    file_id = poll_upload_task_status(job_id)
    SystemLogger.info("上传文件到火山引擎的Job返回的FileId:",file_id)
    
    mediainfo =  get_media_infos(file_id)
    Duration = mediainfo.SourceInfo.AudioStreamMeta.Duration
    print(Duration)

    video_path="https://smartboximagesavecxk.oss-cn-shenzhen.aliyuncs.com/images/20240507075201112_AI生成马斯克婴儿照疯传%23马斯克 %23AI绘画.mp4?Expires=1717660321&OSSAccessKeyId=LTAI5tBBouBKye2QVf8Fop65&Signature=SdwCVJXzrzO%2BsShVJL0bxJho84k%3D"
    video_path,job_status = clear_video_subtitles(video_path)
    print(job_status)

    
    taskId="a403561a5cc8f65b3e1c1ac583a70ca1"
    job_ids = [taskId]
    job_details = poll_job_statusV1( job_ids)
    SystemLogger.info(f'提交擦除视频的task返回的结果:{job_details}')
    '''
    url="http://vv.soraapi.site/53c24d98404d4fa5a89891d4607f36ed?a=0&auth_key=1719893321-b26fab2925524b729f6f79a6a1452e0d-0-eb031adaae658fc23a8d4d087c267ce3&br=12340&bt=12340&cd=0%7C0%7C0&ch=0&cr=0&cs=0&dr=0&ds=4&eid=v0263dg10004cq1mtvqljht0k04p9p2g&er=0&l=20240702110750C2A4A85FA50D0781D5AE&lr=&mime_type=video_mp4&net=0&pl=0&qs=13&rc=anNzMzNrb3lwdDczNGc5M0ApNTw3bndtdHc0ZjMzajY1eWcvNjFocWducS5gLS1kMC9zc2RtbS0tZWlzam4xLS5hMy06Yw%3D%3D&vl=&vr="
    download_video(url)

    #download_video(url)