import subprocess
import os
import shutil
import pysrt
import langcodes
from datetime import datetime
from Logger import SystemLogger
from pydub import AudioSegment
from datetime import datetime
from langdetect import detect

def change_file_extension(file_path, new_extension):
    """
    将文件的扩展名更改为新的扩展名。
    参数：
    - file_path: 原始文件路径
    - new_extension: 新的文件扩展名，如 '.mp3'
    """
    base = os.path.splitext(file_path)[0]
    return base + new_extension

def add_prefix_to_filename(file_path, prefix):
    """
    在文件名前添加指定的前缀，并返回带有前缀的完整文件路径。
    
    参数：
    - file_path: 原始的文件路径
    - prefix: 要添加到文件名前的前缀字符串
    
    返回：
    - 带有前缀的完整文件路径
    """
    # 分离出目录和文件名
    directory, filename = os.path.split(file_path)

    # 在文件名前添加前缀
    new_filename = prefix + filename

    # 将目录和新文件名重新组合成一个完整的路径
    new_file_path = os.path.join(directory, new_filename)
    
    return new_file_path

def combine_path_and_filename(file_path, target_filename):
    """
    合成一个完整的文件路径，使用给定的目录路径和目标文件名。
    
    参数：
    - directory_path: 目录的完整路径
    - target_filename: 要合成的目标文件名
    
    返回：
    - 合成后的完整文件路径
    """
        # 分离出目录和文件名
    directory_path, filename = os.path.split(file_path)

    #target_directory_path, target_filename_temp = os.path.split(target_filename)

    
    # 将目录和文件名组合成一个完整的路径
    full_path = os.path.join(directory_path, target_filename)
    
    return full_path

def getDirectory(file_path):
    """
    只返回路径
    
    参数：
    - file_path: 目录的完整路径


    返回：路径
    -
    """
        # 分离出目录和文件名
    directory_path, filename = os.path.split(file_path)
    

    
    return directory_path


def getFileName(file_path):
    """
    只返回路径
    
    参数：
    - file_path: 目录的完整路径


    返回：路径
    -
    """
        # 分离出目录和文件名
    directory_path, filename = os.path.split(file_path)
    

    
    return filename


def copy_file_to_timestamped_directory(original_path):
    """
    复制文件到一个新的以当前日期时间和原始文件名命名的目录。
    
    参数:
    - original_path: 原始文件的完整路径
    
    返回:
    - 新文件的完整路径
    """
    # 获取原始文件的目录和文件名
    directory, filename = os.path.split(original_path)
    
    # 获取当前日期和时间
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    
    # 创建新的目录名，包括日期时间和原始文件名（不带扩展名）
    base_filename = os.path.splitext(filename)[0]
    new_directory = os.path.join(directory, f"{timestamp}{base_filename}")
    
    # 创建新目录
    if not os.path.exists(new_directory):
        os.makedirs(new_directory)
    
    # 构建新文件的完整路径
    new_file_path = os.path.join(new_directory, filename)
    
    # 复制文件到新位置
    shutil.copy2(original_path, new_file_path)
    
    return new_file_path


def generate_timestamped_filepath(video_path):
    """
    在指定视频路径的目录中生成一个以'soraapi_YYYYMMDDHHMMSS.mp4'格式命名的新文件路径。
    
    参数:
    - video_path: 原始视频文件的路径
    
    返回:
    - 新文件的完整路径
    """
    # 获取原始视频的目录
    directory = os.path.dirname(video_path)
    
    # 获取当前日期和时间
    now = datetime.now()
    timestamp = now.strftime("%Y%m%d%H%M%S")
    
    # 构建新的文件名
   
    filename = f"[Tiktokwit.com]_{timestamp}.mp4"
    
    # 构建新文件的完整路径
    new_file_path = os.path.join(directory, filename)
    
    return new_file_path


def generate_osskey(file_name):
    """
    生成上传文件的key，格式为'images/年月日时分秒毫秒_文件名'。
    
    参数:
    - file_name: 文件名
    
    返回:
    - 生成的key字符串
    """
    # 获取当前时间，并格式化为'年月日时分秒毫秒'格式
    current_time = datetime.now().strftime('%Y%m%d%H%M%S%f')
    # 生成并返回key
    return f"images/{current_time}_{file_name}"



def insert_blank_subtitle(srt_file_path, output_file_path, min_gap_ms=500):
    """
    在指定的SRT字幕文件中插入空白字幕，仅在时间间隔大于min_gap_ms时插入空白字幕。

    Args:
        srt_file_path (str): 输入的SRT字幕文件路径。
        output_file_path (str): 输出的SRT字幕文件路径。
        min_gap_ms (int, optional): 最小时间间隔，单位毫秒。默认为500毫秒。

    Returns:
        None: 此函数没有返回值，直接将结果保存到output_file_path指定的文件中。

    """
    subs = pysrt.open(srt_file_path)
    blank_subs = pysrt.SubRipFile()

    for i in range(len(subs) - 1):
        end_time = subs[i].end
        start_time = subs[i+1].start
        
        # 计算时间间隔
        time_difference = (start_time - end_time).ordinal
        
        # 仅在时间间隔大于min_gap_ms时插入空白字幕
        if time_difference > min_gap_ms:
            blank_sub = pysrt.SubRipItem(index=len(blank_subs) + 1, start=end_time, end=start_time, text="   ")
            blank_subs.append(blank_sub)

    # 添加原始字幕
    for sub in subs:
        blank_subs.append(sub)

    # 重新排序字幕索引
    blank_subs.sort()
    for i, sub in enumerate(blank_subs):
        sub.index = i + 1

    # 保存结果到新的SRT文件
    blank_subs.save(output_file_path, encoding='utf-8')


def check_subtitle_content(filename):
    """
    检查指定的.srt字幕文件是否包含超过3行的字幕文本。

    参数:
    - filename: 字幕文件的路径

    返回:
    - 如果字幕行数超过3行，则返回 True
    - 如果字幕行数不超过3行或文件读取失败，则返回 False
    """
    try:
        # 初始化字幕行计数器
        subtitle_count = 0
        
        # 打开文件并读取
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                # 去除每行的首尾空格
                stripped_line = line.strip()
                
                # 检查处理过的行是否为空
                if stripped_line:
                    # 如果行不包含时间码（通常时间码格式如 '00:00:01,000 --> 00:00:04,000'）
                    if '-->' not in stripped_line:
                        # 计数有效的字幕行
                        subtitle_count += 1

        # 判断字幕行数是否超过3行
        if subtitle_count > 3:
            return True
        else:
            return False
            
    except FileNotFoundError:
        # 如果文件不存在，则打印错误信息并返回 False
        print(f"文件 {filename} 未找到。")
        return False
    except Exception as e:
        # 处理其他可能的错误
        print(f"发生错误：{e}")
        return False
    

def adjust_empty_subtitles(file_path: str) -> None:
    # Read the contents of the file
    with open(file_path, 'r', encoding='utf-8') as file:
        subtitles = file.read()
    
    # Split the input string into lines
    lines = subtitles.split('\n')
    
    # Initialize a list to hold the adjusted lines
    adjusted_lines = []
    
    # Iterate over the lines
    for i in range(len(lines) - 1):
        # Add the current line to the adjusted lines
        adjusted_lines.append(lines[i])
        
        # Check if the current line is a subtitle time line and the next line is empty
        if '-->' in lines[i] and lines[i + 1].strip() == '':
            # Add a new line with a single space before the empty line
            adjusted_lines.append(' ')
    
    # Add the last line
    adjusted_lines.append(lines[-1])
    
    # Join the adjusted lines into a single string
    adjusted_subtitles = '\n'.join(adjusted_lines)
    
    # Write the adjusted subtitles back to the file
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(adjusted_subtitles)



import pysrt
from langdetect import detect

def detect_srt_language(file_path):
    """
    检测 SRT 文件中字幕的语言。

    参数:
        file_path (str): SRT 文件的路径。

    返回:
        str: 检测到的 SRT 文件的语言代码。
    """
    # 读取SRT文件
    subs = pysrt.open(file_path)
    
    # 初始化用于存储前10段字幕文本的字符串
    text = ""
    
    # 提取前10段的内容并拼接成一个字符串
    for i in range(min(10, len(subs))):
        text += subs[i].text_without_tags + " "
    
    # 检测语言
    language = detect(text)
    language_name = langcodes.Language.get(language).language_name('zh')

    
    return language_name


import socket

def get_machine_name():
    """
    尝试获取当前机器的IP地址作为机器名。
    如果无法获取IP地址，则返回一个默认的机器名。

    返回:
    - str: 机器名（IP地址或默认值）
    """
    try:
        # 尝试获取当前机器的IP地址
        machine_name = socket.gethostbyname(socket.gethostname())
    except socket.gaierror:
        # 如果获取IP地址失败，记录日志并使用默认机器名
        SystemLogger.info("无法获取IP地址，使用默认机器名。")
        machine_name = "default_machine"
    return str(machine_name)

def generate_silence(duration_ms, output_path):
    #取得空白声音
    #duration_ms：输入空白声音时长
    #output_path：输入空白声音路径
    silence = AudioSegment.silent(duration=duration_ms)
    silence.export(output_path, format="mp3")



if __name__ == "__main__":
    #print(get_machine_name())
    english_subtitles_file=r"E:\AIHelp\v1.16-gtp4_o_plus_english\20240531154252666\666_english.srt"
    adjust_empty_subtitles(english_subtitles_file)

