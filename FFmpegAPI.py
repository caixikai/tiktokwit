import subprocess
import os
import subprocess
from util import getFileName
from pydub import AudioSegment

#1.视频mp4转音频 ===================================

def extract_audio_from_video(video_path, audio_output_path):
    """
    使用ffmpeg从给定的视频文件中提取音频，并保存为MP3格式。
    参数：
    - video_path: 视频文件的路径
    - audio_output_path: 音频输出文件的路径
    """
    if os.path.exists(audio_output_path):
        print(f"找到已存在的文件 {audio_output_path}，正在删除...")
        os.remove(audio_output_path)
    
    command = [
        'ffmpeg',
        '-i', video_path,      # 输入视频文件路径
        '-q:a', '0',           # 指定音频质量。这里0表示最佳质量
        '-map', 'a',           # 选择音频流
        audio_output_path      # 输出音频文件路径
    ]
    
    try:
        # 执行ffmpeg命令
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print('音频提取成功，输出文件为:', audio_output_path)
    except subprocess.CalledProcessError as e:
        print('ffmpeg处理错误:', e.stderr)
 
#1.==============================================
        

#5 合并英文语音和视频==============================================================


def merge_video_audio(video_path, background_audio_path, translation_audio_path, output_video_path):
    """
    将视频与背景音和翻译音轨合并到一起，并自动调整音量。

    参数：
    - video_path: 输入视频文件的路径
    - background_audio_path: 背景音音频文件的路径
    - translation_audio_path: 翻译音轨音频文件的路径
    - output_video_path: 输出合并视频文件的路径
    """
    # 检查文件是否存在，如果存在，则删除
    if os.path.exists(output_video_path):
        os.remove(output_video_path)

    command = [
        'ffmpeg',
        '-i', video_path,                      # 输入视频文件
        '-i', background_audio_path,           # 输入背景音
        '-i', translation_audio_path,          # 输入翻译音轨
        '-filter_complex', '[1:a][2:a]amerge=inputs=2[a];[a]dynaudnorm[a]',  # 合并音轨并应用动态音量标准化
        '-map', '0:v',                         # 映射视频轨
        '-map', '[a]',                         # 映射合并后的音轨
        '-c:v', 'copy',                        # 视频轨道直接拷贝
        '-c:a', 'aac',                         # 音频编码
        '-strict', 'experimental',             # 允许实验特性
        output_video_path                      # 输出文件
    ]

    subprocess.run(command, check=True)
    return output_video_path




def merge_video_audioV1(video_path, background_audio_path, translation_audio_path, output_video_path):
    """
    将视频与背景音和翻译音轨合并到一起。

    参数：
    - video_path: 输入视频文件的路径
    - background_audio_path: 背景音音频文件的路径
    - translation_audio_path: 翻译音轨音频文件的路径
    - output_video_path: 输出合并视频文件的路径
    """
    # 检查文件是否存在，如果存在，则删除
    if os.path.exists(output_video_path):
        os.remove(output_video_path)

    command = [
        'ffmpeg',
        '-i', video_path,                      # 输入视频文件
        '-i', background_audio_path,           # 输入背景音
        '-i', translation_audio_path,          # 输入翻译音轨
        '-filter_complex', '[1:a][2:a]amerge=inputs=2[a]',  # 合并音轨
        '-map', '0:v',                         # 映射视频轨
        '-map', '[a]',                         # 映射合并后的音轨
        '-c:v', 'copy',                        # 视频轨道直接拷贝
        '-c:a', 'aac',                         # 音频编码
        '-strict', 'experimental',             # 允许实验特性
        output_video_path                      # 输出文件
    ]

    subprocess.run(command, check=True)
    return output_video_path

'''
#5.===============================================================================
'''

#7.把字幕是英语视频烧录在一起


def burn_subtitles_into_video(video_path, subtitles_path, output_video_path):
    """
    使用ffmpeg将字幕烧录到视频文件中，并保存为新的视频文件。
    
    参数：
    - video_path: 视频文件的路径
    - subtitles_path: 字幕文件的路径（SRT文件）
    - output_video_path: 输出视频文件的路径
    """
    if os.path.exists(output_video_path):
        print(f"找到已存在的文件 {output_video_path}，正在删除...")
        os.remove(output_video_path)
    
    command = [
        'ffmpeg',
        '-i', video_path,                        # 输入视频文件路径
        '-vf', f"subtitles={subtitles_path}",    # 设置视频滤镜以烧录字幕
        output_video_path                        # 输出视频文件路径
    ]
    
    try:
        # 执行ffmpeg命令
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print('字幕烧录成功，输出文件为:', output_video_path)
    except subprocess.CalledProcessError as e:
        print('ffmpeg处理错误:', e.stderr)

def convert_srt_to_ass(srt_path):
    """
    使用FFmpeg将SRT格式的字幕文件转换为ASS格式，并返回ASS文件路径。
    
    参数：
    - srt_path: SRT字幕文件的路径。
    
    返回：
    - ASS字幕文件的路径。
    """
    # 从SRT文件路径生成ASS文件路径
    base_name = os.path.splitext(srt_path)[0]
    ass_path = f"{base_name}.ass"
    
    if os.path.exists(ass_path):
        print(f"找到已存在的文件 {ass_path}，正在删除...")
        os.remove(ass_path)
    
    command = ['ffmpeg', '-i', srt_path, ass_path]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"转换成功，输出文件为: {ass_path}")
        return ass_path  # 返回生成的ASS文件路径
    except subprocess.CalledProcessError as e:
        print("转换失败:", e.stderr)
        return None



def convert_srt_to_assV2(srt_path, subtitle_height_percent=10, font_color="&H00FFFFFF"):
    """
    使用FFmpeg将SRT格式的字幕文件转换为ASS格式，并调整字幕的高度和字体颜色。
    
    参数：
    - srt_path: SRT字幕文件的路径。
    - subtitle_height_percent: 字幕距离视频底部的高度百分比。
    - font_color: 字体颜色的ASS十六进制字符串（如：'&H00FFFFFF'为白色）。
    
    返回：
    - ASS字幕文件的路径。
    """
    # 从SRT文件路径生成ASS文件路径
    base_name = os.path.splitext(srt_path)[0]
    ass_path = f"{base_name}.ass"
    
    if os.path.exists(ass_path):
        print(f"找到已存在的文件 {ass_path}，正在删除...")
        os.remove(ass_path)
    
    # 调用FFmpeg转换字幕
    command = ['ffmpeg', '-i', srt_path, ass_path]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"转换成功，输出文件为: {ass_path}")
    except subprocess.CalledProcessError as e:
        print("转换失败:", e.stderr)
        return None
    
    # 读取ASS文件内容
    with open(ass_path, 'r', encoding='utf-8') as file:
        ass_content = file.readlines()
    
    # 修改字幕颜色和位置
    for i, line in enumerate(ass_content):
        if line.startswith("Style: Default"):
            parts = line.split(',')
            # 修改字体颜色
            parts[4] = font_color
            # 假设视频高度为1080p，根据比例计算MarginV的像素值
            parts[-2] = str(int(1080 * (subtitle_height_percent / 100)))
            ass_content[i] = ','.join(parts)
            break
    
    # 保存修改后的ASS内容
    with open(ass_path, 'w', encoding='utf-8') as file:
        file.writelines(ass_content)
    
    return ass_path  # 返回修改后的ASS文件路径

def convert_srt_to_assV3(srt_path, subtitle_height_percent=10, font_color="&H0000FF&"):
    base_name = os.path.splitext(srt_path)[0]
    ass_path = f"{base_name}.ass"
    
    if os.path.exists(ass_path):
        print(f"找到已存在的文件 {ass_path}，正在删除...")
        os.remove(ass_path)
    
    command = ['ffmpeg', '-i', srt_path, ass_path]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"转换成功，输出文件为: {ass_path}")
    except subprocess.CalledProcessError as e:
        print("转换失败:", e.stderr)
        return None
    
    with open(ass_path, 'r', encoding='utf-8') as file:
        ass_content = file.readlines()
    
    for i, line in enumerate(ass_content):
        if line.startswith("Style:"):
            parts = line.split(',')
            parts[3] = font_color
            parts[-2] = str(int(1080 * (subtitle_height_percent / 100)))
            ass_content[i] = ','.join(parts)
    
    with open(ass_path, 'w', encoding='utf-8') as file:
        file.writelines(ass_content)
    
    return ass_path

def convert_srt_to_assV5(srt_path, subtitle_height_percent=10, font_color="&H0000FF&", languagename="英文"):
    base_name = os.path.splitext(srt_path)[0]
    ass_path = f"{base_name}.ass"
    
    if os.path.exists(ass_path):
        print(f"找到已存在的文件 {ass_path}，正在删除...")
        os.remove(ass_path)
    
    # 使用ffmpeg将SRT格式字幕转换为ASS格式字幕
    command = ['ffmpeg', '-i', srt_path, ass_path]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"转换成功，输出文件为: {ass_path}")
    except subprocess.CalledProcessError as e:
        print("转换失败:", e.stderr)
        return None
    
    # 读取转换后的ASS文件内容，并修改字体颜色和字幕高度
    with open(ass_path, 'r', encoding='utf-8') as file:
        ass_content = file.readlines()
    
    for i, line in enumerate(ass_content):
        if line.startswith("Style:"):
            parts = line.split(',')
            parts[3] = font_color
            parts[-2] = str(int(1080 * (subtitle_height_percent / 100)))
            # 根据语言设置字幕样式
            if languagename.lower() in ["阿拉伯语", "波斯语", "乌尔都语"]:
                parts[-3] = "RTL"  # 设置文本方向为从右到左
                parts[1] = "Scheherazade"  # 设置字体为Scheherazade
            ass_content[i] = ','.join(parts)
    
    # 将修改后的内容写回ASS文件
    with open(ass_path, 'w', encoding='utf-8') as file:
        file.writelines(ass_content)
    
    return ass_path



def ensure_directory_exists(path):
    """
    确保文件的目录存在，如果不存在，则创建。
    """
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"创建目录：{directory}")

def burn_subtitles_into_videoV3(video_path, subtitles_path, output_video_path, font_size=24, subtitle_height_percent=10, font_color="&H00FFFFFF"):
    subtitles_path = convert_srt_to_assV3(subtitles_path, subtitle_height_percent, font_color)

    """
    使用ffmpeg将字幕烧录到视频文件中，并保存为新的视频文件。

    参数：
    - video_path: 视频文件的路径
    - subtitles_path: 字幕文件的路径（应为ASS格式以支持样式调整）
    - output_video_path: 输出视频文件的路径
    - font_size: 字幕字体大小
    """
    ensure_directory_exists(output_video_path)

    if os.path.exists(output_video_path):
        print(f"找到已存在的文件 {output_video_path}，正在删除...")
        os.remove(output_video_path)


    # 使用ffmpeg的subtitles滤镜烧录字幕，':force_style'选项允许我们设置样式，如字体大小
    #subtitles_path = r"E:\AIHelp\v1.11\20240420\final_20240329V1.ass"
    # 为ffmpeg命令转义路径
    escaped_subtitles_path = subtitles_path.replace('\\', '\\\\').replace(':', '\\:')

    subtitles_filter = f"subtitles='{escaped_subtitles_path}':force_style='FontSize={font_size}'"

    print(subtitles_filter)

    command = [
        'ffmpeg',
        '-i', video_path,  # 输入视频文件路径
        '-vf', subtitles_filter,  # 设置视频滤镜以烧录字幕并调整字体大小
        '-c:v', 'libx264',  # 指定视频编码器
        '-crf', '23',  # 设置输出视频的质量，值越小质量越高
        '-preset', 'fast',  # 编码速度与压缩率的平衡
        output_video_path  # 输出视频文件路径
    ]

    try:
        # 执行ffmpeg命令
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print('字幕烧录成功，输出文件为:', output_video_path)
    except subprocess.CalledProcessError as e:
        print('ffmpeg处理错误:', e.stderr)


def burn_subtitles_into_videoV5(video_path, subtitles_path, output_video_path, font_size=24, subtitle_height_percent=10, font_color="&H00FFFFFF",languagename="英文"):
    subtitles_path = convert_srt_to_assV5(subtitles_path, subtitle_height_percent, font_color,languagename=languagename)
    """
    使用ffmpeg将字幕烧录到视频文件中，并保存为新的视频文件。

    Args:
        video_path (str): 视频文件的路径。
        subtitles_path (str): 字幕文件的路径（应为ASS格式以支持样式调整）。
        output_video_path (str): 输出视频文件的路径。
        font_size (int, optional): 字幕字体大小。默认为24。
        subtitle_height_percent (int, optional): 字幕高度占视频高度的百分比。默认为10。
        font_color (str, optional): 字幕颜色，格式为ffmpeg的ass样式颜色。默认为白色（&H00FFFFFF）。
        languagename (str, optional): 字幕的语言名称。默认为"英文"。

    Returns:
        None

    """

    if languagename.lower() in ["阿拉伯语", "波斯语", "乌尔都语"]:
        font_size=20


    ensure_directory_exists(output_video_path)

    if os.path.exists(output_video_path):
        print(f"找到已存在的文件 {output_video_path}，正在删除...")
        os.remove(output_video_path)


    # 使用ffmpeg的subtitles滤镜烧录字幕，':force_style'选项允许我们设置样式，如字体大小
    #subtitles_path = r"E:\AIHelp\v1.11\20240420\final_20240329V1.ass"
    # 为ffmpeg命令转义路径
    escaped_subtitles_path = subtitles_path.replace('\\', '\\\\').replace(':', '\\:')

    #subtitles_filter = f"subtitles='{escaped_subtitles_path}':force_style='FontSize={font_size}'"
    subtitles_filter = f"subtitles='{escaped_subtitles_path}'"
    print(subtitles_filter)

    #ffmpeg -i final_666.mp4 -vf "final_666.ass" final_666_222.mp4

    command = [
        'ffmpeg',
        '-i', video_path,  # 输入视频文件路径
         '-vf', subtitles_filter,  # 设置视频滤镜以烧录字幕并调整字体大小, 
        output_video_path  # 输出视频文件路径
    ]

    try:
        # 执行ffmpeg命令
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print('字幕烧录成功，输出文件为:', output_video_path)
    except subprocess.CalledProcessError as e:
        print('ffmpeg处理错误:', e.stderr)


def burn_subtitles_into_videoV2(video_path, subtitles_path, output_video_path, font_size=24,subtitle_height_percent=10,font_color="&H00FFFFFF"):
    subtitles_path= convert_srt_to_assV3(subtitles_path,subtitle_height_percent,font_color )

    """
    使用ffmpeg将字幕烧录到视频文件中，并保存为新的视频文件。

    Args:
        video_path (str): 视频文件的路径。
        subtitles_path (str): 字幕文件的路径（应为ASS格式以支持样式调整）。
        output_video_path (str): 输出视频文件的路径。
        font_size (int, optional): 字幕字体大小。默认为24。
        subtitle_height_percent (int, optional): 字幕高度的百分比（用于字幕ASS文件的生成）。默认为10。
        font_color (str, optional): 字幕颜色（十六进制颜色码）。默认为白色（&H00FFFFFF）。

    Returns:
        None

    Raises:
        subprocess.CalledProcessError: 当ffmpeg命令执行失败时引发异常。

    """
    if os.path.exists(output_video_path):
        print(f"找到已存在的文件 {output_video_path}，正在删除...")
        os.remove(output_video_path)
    
    subtitles_path= getFileName(subtitles_path)

    # 使用ffmpeg的subtitles滤镜烧录字幕，':force_style'选项允许我们设置样式，如字体大小
    subtitles_filter = f"subtitles='{subtitles_path}':force_style='FontSize={font_size}'"
    
    command = [
        'ffmpeg',
        '-i', video_path,                         # 输入视频文件路径
        '-vf', subtitles_filter,                  # 设置视频滤镜以烧录字幕并调整字体大小
        output_video_path                         # 输出视频文件路径
    ]
    
    try:
        # 执行ffmpeg命令
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print('字幕烧录成功，输出文件为:', output_video_path)
    except subprocess.CalledProcessError as e:
        print('ffmpeg处理错误:', e.stderr)

import os
import subprocess

def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

def convert_srt_to_assV6(srt_path, subtitle_height_percent=10, font_color="&H00FFFFFF", languagename="英文"):
    base_name = os.path.splitext(srt_path)[0]
    ass_path = f"{base_name}.ass"

    if os.path.exists(ass_path):
        print(f"找到已存在的文件 {ass_path}，正在删除...")
        os.remove(ass_path)

    command = ['ffmpeg', '-i', srt_path, ass_path]
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"转换成功，输出文件为: {ass_path}")
    except subprocess.CalledProcessError as e:
        print("转换失败:", e.stderr)
        return None

    with open(ass_path, 'r', encoding='utf-8') as file:
        ass_content = file.readlines()

    for i, line in enumerate(ass_content):
        if line.startswith("Style:"):
            parts = line.split(',')
            parts[3] = font_color
            parts[2] = str(24)  # 字体大小
            parts[-2] = str(int(1080 * (subtitle_height_percent / 100)))

            if languagename.lower() in ["阿拉伯语", "波斯语", "乌尔都语"]:
                parts[-3] = "1"  # 设置RTL
                parts[1] = "Scheherazade"  # 确保使用支持阿拉伯语的字体
            else:
                parts[-3] = "0"  # 其他语言默认LTR

            ass_content[i] = ','.join(parts)

    with open(ass_path, 'w', encoding='utf-8') as file:
        file.writelines(ass_content)

    return ass_path

def burn_subtitles_into_videoV6(video_path, subtitles_path, output_video_path, font_size=24, subtitle_height_percent=10, font_color="&H00FFFFFF", languagename="英文"):
    subtitles_path = convert_srt_to_assV5(subtitles_path, subtitle_height_percent, font_color, languagename=languagename)

    if languagename.lower() in ["阿拉伯语", "波斯语", "乌尔都语"]:
        font_size = 20

    ensure_directory_exists(output_video_path)

    if os.path.exists(output_video_path):
        print(f"找到已存在的文件 {output_video_path}，正在删除...")
        os.remove(output_video_path)

    escaped_subtitles_path = subtitles_path.replace('\\', '\\\\').replace(':', '\\:')

    subtitles_filter = f"subtitles='{escaped_subtitles_path}'"

    print(subtitles_filter)

    command = [
        'ffmpeg',
        '-i', video_path,
        '-vf', subtitles_filter,
        '-c:v', 'libx264',
        '-crf', '23',
        '-preset', 'fast',
        output_video_path
    ]

    try:
        result = subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        print('字幕烧录成功，输出文件为:', output_video_path)
    except subprocess.CalledProcessError as e:
        print('ffmpeg处理错误:', e.stderr)



if __name__ == "__main__":
    # 需要提供输入视频文件路径和SRT字幕文件路径

    burn_subtitles_into_videoV5("input_video.mp4", "/mnt/data/666_english.srt", "output_video.mp4", languagename="阿拉伯语")

