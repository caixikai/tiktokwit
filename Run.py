
import subprocess
import os
import time
import VolcengineAPI

from CheckMP3Time import Check_Chinese_English_srtFile, csv_to_srt, extract_audio_paths_from_csv, merge_to_csv, update_csv_with_adjustmentsV3
from Logger import SystemLogger
from MusicSourceSeparateAPI import separate_background_audio
from OssAPI import *
from GPTAPI import *
from FFmpegAPI import *
from VideoAPI import retry
from datetime import datetime
from VolcengineAPI import clear_video_subtitles, get_media_infos, poll_upload_task_status
from util import add_prefix_to_filename, adjust_empty_subtitles, change_file_extension, check_subtitle_content, combine_path_and_filename, copy_file_to_timestamped_directory, detect_srt_language, generate_timestamped_filepath,  insert_blank_subtitle




@retry(attempts=3, delay=5, error_message="视频提取音频失败。")
def extract_audio_retry(video_path, audio_output_path):
    extract_audio_from_video(video_path, audio_output_path)

@retry(attempts=3, delay=5, error_message="上传音频文件失败。")
def upload_audio_retry(audio_output_path):
    return upload_and_get_signed_url(audio_output_path)

@retry(attempts=3, delay=5, error_message="分离背景音频失败。")
def extract_background_audio_retry(audio_output_path, background_mp3_file):
    return separate_background_audio(audio_output_path, background_mp3_file)

@retry(attempts=3, delay=5, error_message="音频识别失败。")
def recognize_audio_retry(appid, token, cluster, audio_url, language, output_file):
    gptranslator = GPTTranslator()
    return gptranslator.file_recognizeV2(appid, token, cluster, audio_url, language, output_file)

@retry(attempts=3, delay=5, error_message="检测字幕语言失败。")
def detect_language_retry(chinese_subtitles_file):
    return detect_srt_language(chinese_subtitles_file)

@retry(attempts=3, delay=5, error_message="检查字幕内容失败。")
def check_content_retry(chinese_subtitles_file):
    return check_subtitle_content(chinese_subtitles_file)

@retry(attempts=3, delay=5, error_message="插入空白字幕失败。")
def insert_blank_retry(chinese_subtitles_file):
    insert_blank_subtitle(chinese_subtitles_file, chinese_subtitles_file)

@retry(attempts=3, delay=5, error_message="字幕翻译失败。")
def translate_subtitles_retry(chinese_subtitles_file, source_language_name, languagename):
    gptranslator = GPTTranslator()
    return gptranslator.translate_subtitles_to_english(chinese_subtitles_file, source_language_name, languagename)

@retry(attempts=3, delay=5, error_message="调整空白字幕失败。")
def adjust_empty_retry(english_subtitles_file):
    adjust_empty_subtitles(english_subtitles_file)

@retry(attempts=3, delay=5, error_message="字幕合并为CSV失败。")
def merge_subtitles_retry(english_subtitles_file, chinese_subtitles_file, csv_file):
    merge_to_csv(english_subtitles_file, chinese_subtitles_file, csv_file)

@retry(attempts=3, delay=5, error_message="更新CSV文件失败。")
def update_csv_retry(csv_file, languagename):
    return update_csv_with_adjustmentsV3(csv_file, languagename)

@retry(attempts=3, delay=5, error_message="从CSV提取音频路径失败。")
def extract_audio_paths_retry(csv_file):
    return extract_audio_paths_from_csv(csv_file)

@retry(attempts=3, delay=5, error_message="合并音频段失败。")
def merge_audio_retry(audio_paths, english_merged_audio_file):
    gptranslator = GPTTranslator()
    return gptranslator.merge_audio_segments(audio_paths, english_merged_audio_file)

@retry(attempts=3, delay=5, error_message="合并视频和音频失败。")
def merge_video_retry(video_path, background_mp3_file, english_merged_audio_file, output_path):
    return merge_video_audio(video_path, background_mp3_file, english_merged_audio_file, output_path)

@retry(attempts=3, delay=5, error_message="CSV转SRT文件失败。")
def csv_to_srt_file_retry(adjust_csv_file, output_srt_file):
    return csv_to_srt(adjust_csv_file, output_srt_file)

@retry(attempts=3, delay=5, error_message="字幕烧录到视频失败。")
def burn_subtitles_retry(video_path, english_subtitles_file, final_all_filename):
    burn_subtitles_into_videoV3(video_path, english_subtitles_file, final_all_filename, font_size=10, subtitle_height_percent=5, font_color="&H00DE")



def translatevideoV3( video_path, languagename):
    """
    将视频翻译成指定语言的视频文件。

    Args:
        video_path (str): 视频文件路径。
        languagename (str): 目标语言名称。

    Returns:
        Union[str, None]: 合并后的视频文件路径（如果成功），否则返回None。

    Raises:
        无特定异常，但处理过程中发生的异常将被捕获并记录。

    """
    try:
        #创建GPT翻译对象
        gptranslator = GPTTranslator()

        SystemLogger.info("=======================================")
        SystemLogger.info("1.视频mp4转音频=========================")
        audio_output_path = change_file_extension(video_path, '.mp3')
        extract_audio_retry(video_path, audio_output_path)
        audio_url = upload_audio_retry(audio_output_path)
        SystemLogger.info(f"1.视频转音频输出的mp3文件是 {audio_output_path}")
        SystemLogger.info(f"视频转音频输出的mp3文件url是 {audio_url}")

        SystemLogger.info("1.1.音频提取背景音=========================")
        background_mp3_file = change_file_extension(audio_output_path, '.mp3')
        background_mp3_file = add_prefix_to_filename(background_mp3_file, 'background_mp3_')
        background_mp3_file = extract_background_audio_retry(audio_output_path, background_mp3_file)
        SystemLogger.info(f"1.1.音频提取背景音输出的mp3文件是 {background_mp3_file}")

        SystemLogger.info("2.音频转字幕srt文件=========================")

        chinese_subtitles_file = change_file_extension(video_path, '.srt')
        chinese_subtitles_file = recognize_audio_retry(SysConfig.volcengine_srt_appid, SysConfig.volcengine_srt_token, SysConfig.volcengine_srt_cluster, audio_url, "zh-CN", chinese_subtitles_file)
        SystemLogger.info(f"2.音频转中文字幕srt文件是 {chinese_subtitles_file}")

        source_language_name = detect_language_retry(chinese_subtitles_file)


        if source_language_name == languagename:
            raise Exception("原语言和配音语言是一样的！")

        checkcontent_result = check_content_retry(chinese_subtitles_file)
        SystemLogger.info(f"2.1检查{source_language_name}字幕srt文件是否为空 {checkcontent_result}")

        if not checkcontent_result:
            SystemLogger.info('字幕文件为空,直接返回失败')
            return

        insert_blank_retry(chinese_subtitles_file)
        SystemLogger.info(f"2.2 {source_language_name}字幕srt文件如果有时间间隔，则插入空白字幕是 {chinese_subtitles_file}")

        check_result = False
        retry_count = 3
    
        while retry_count > 0 and not check_result:
            SystemLogger.info(f"3.{source_language_name}字幕变成{languagename}字幕=========================")
            english_subtitles_file = translate_subtitles_retry(chinese_subtitles_file, source_language_name, languagename)
            SystemLogger.info(f"3.{source_language_name}字幕变成{languagename}字幕srt文件是 {english_subtitles_file}")

            adjust_empty_retry(english_subtitles_file)
            SystemLogger.info(f"3.1 {languagename}字幕srt文件如果没有空白字符行，则插入空白字幕是 {english_subtitles_file}")

            #检查中文和英文的字幕段落数目是否一致，不一致则重试3次
            check_result = Check_Chinese_English_srtFile(chinese_subtitles_file, english_subtitles_file)
            if check_result:
                break
            retry_count -= 1

        english_merged_audio_file = change_file_extension(english_subtitles_file, '.mp3')
        english_merged_audio_file = gptranslator.srt_to_audio(english_subtitles_file,english_merged_audio_file)
        SystemLogger.info(f"3.1.1 生成{languagename}字幕的音频文件")


        SystemLogger.info(f"3.2.校验{languagename}字幕文件=========================")
        SystemLogger.info(f"3.2.1 {source_language_name}字幕和{languagename}字幕文件信息合并成.csv文件=========================")
        csv_file = change_file_extension(english_subtitles_file, '.csv')
        merge_subtitles_retry(english_subtitles_file, chinese_subtitles_file, csv_file)
        SystemLogger.info(csv_file)
        SystemLogger.info(languagename)

        SystemLogger.info(f"3.2.2 根据csv文件,验证{source_language_name}mp3文件=========================")
        adjust_csv_file = update_csv_retry(csv_file, languagename)
        SystemLogger.info(adjust_csv_file)

        SystemLogger.info(f"3.2.3合并校验后的{source_language_name}mp3文件=========================")
        english_merged_audio_file = change_file_extension(english_subtitles_file, '.mp3')
        audio_paths = extract_audio_paths_retry(adjust_csv_file)
        english_merged_audio_file = merge_audio_retry(audio_paths, english_merged_audio_file)
        SystemLogger.info(english_merged_audio_file)

        SystemLogger.info(f"4.{languagename}的字幕文件变成{languagename}语音的文件是 {english_merged_audio_file}")

        SystemLogger.info(f"5.开始合并{languagename}语音和视频 ")
        output_path= add_prefix_to_filename(video_path,'final_')
        video_path = merge_video_retry(video_path, background_mp3_file, english_merged_audio_file, output_path)
        SystemLogger.info(f"5.结束合并{languagename}语音和视频 {video_path}")

        SystemLogger.info(f"6.从csv文件中输出{languagename}字幕=========================")
        english_subtitles_file = change_file_extension(video_path, '.srt')
        english_subtitles_file = csv_to_srt_file_retry(adjust_csv_file, english_subtitles_file)

        SystemLogger.info(f"7.把{languagename}字幕和{languagename}视频烧录在一起=========================")
        final_all_filename = generate_timestamped_filepath(video_path)
        SystemLogger.info(f'video_path= {video_path}')
        SystemLogger.info(f'english_subtitles_file= {english_subtitles_file}')
        SystemLogger.info(f'final_all_filename= {final_all_filename}')

        burn_subtitles_retry(video_path, english_subtitles_file, final_all_filename)

    except Exception as ex:
        error_message = str(ex)
        if len(error_message) > 4000:
            error_message = error_message[:4000]
        SystemLogger.error(f'处理过程中发生错误: {error_message}')

        return None


def get_audio_durationV3(video_path):
    audio_output_path = change_file_extension(video_path, '.mp3')
    extract_audio_from_video(video_path, audio_output_path)

    """ 获取音频文件的时长，单位为秒 """
    audio = AudioSegment.from_file(audio_output_path)
    return len(audio) / 1000.0  # pydub 返回的时长是毫秒，这里转换为秒



def get_audio_durationV5(video_path):

    SystemLogger.info(f'开始推送OSS文件到火山:{video_path}' )
    job_id = VolcengineAPI.upload_video(video_path)
    SystemLogger.info(f'用过URL上传文件到火山引擎的JobID:{job_id}' )
    #查询视频是否上传成功
    file_id = poll_upload_task_status(job_id)
    SystemLogger.info("上传文件到火山引擎的Job返回的FileId:",file_id)
    
    mediainfo =  get_media_infos(file_id)
    Duration = mediainfo.SourceInfo.AudioStreamMeta.Duration
    SystemLogger.info(f'Vid:{file_id}  Duration:f{Duration}')

    return Duration


    

import shutil

if __name__ == "__main__":

    video_path = r'E:\AIHelp_Share\MP4\20240329.mp4'

    current_file_path = os.path.abspath(__file__)
    video_path= combine_path_and_filename(current_file_path,video_path)
    video_path = copy_file_to_timestamped_directory(video_path)

    language_name = "英语"

    result = translatevideoV3(video_path,language_name)
    print(result)








