import csv
import os
import shutil
from datetime import datetime, timedelta
from ctypes import util
from datetime import datetime, timedelta
from mutagen.mp3 import MP3
from GPTAPI import GPTModel, GPTTranslator
from Logger import SystemLogger
from util import add_prefix_to_filename, combine_path_and_filename, generate_silence, getDirectory
from tempfile import NamedTemporaryFile



def get_mp3_duration_ms(file_path):
    audio = MP3(file_path)
    duration_seconds = audio.info.length  # 获取时长，单位为秒
    duration_ms = int(duration_seconds * 1000)  # 转换为毫秒，并取整
    return duration_ms

# SRT时间格式转换为毫秒
def srt_time_to_ms(srt_time):
    time_parts = datetime.strptime(srt_time, '%H:%M:%S,%f')
    delta = timedelta(hours=time_parts.hour, minutes=time_parts.minute, seconds=time_parts.second, microseconds=time_parts.microsecond)
    return int(delta.total_seconds() * 1000)
import re

# 解析SRT文件
def parse_srt(srt_file):
    with open(srt_file, encoding='utf-8') as f:

        lines = f.read().split('\n\n')
        subtitles = []
        for block in lines:
            if block:
                parts = block.split('\n')

                try:
                    index = int(parts[0])
                except ValueError:
                    # 如果无法将 parts[0] 转换为整数，打印错误信息并跳过这个字幕块
                    SystemLogger._logger(f"不能转换成整型，跳过这一行:{block}")
                    continue

                times = parts[1].split(' --> ')
                start_ms = srt_time_to_ms(times[0])
                end_ms = srt_time_to_ms(times[1])
                text = '\n'.join(parts[2:])
                subtitles.append((index, times[0], times[1], start_ms, end_ms, text))
    return subtitles


#检查源中文和英文的srt段落是否数目是否一致
def Check_Chinese_English_srtFile(english_srt, chinese_srt):
    eng_subs = parse_srt(english_srt)
    ch_subs = parse_srt(chinese_srt)

    if len(eng_subs)== len(ch_subs):
        return True
    else:
        return False

# 合并和写入CSV
def merge_to_csv(english_srt, chinese_srt, csv_file):
    eng_subs = parse_srt(english_srt)
    ch_subs = parse_srt(chinese_srt)
    with open(csv_file, mode='w', newline='', encoding='utf-8-sig') as file:  # 使用utf-8-sig编码写入BOM

        writer = csv.writer(file)
        writer.writerow(['序号', '开始时间', '结束时间', '时长(ms)', '英文字幕', '中文字幕', '生成的音频文件名', '音频文件时长', '时长差',
                         '校验后英文字幕', '校验后英文字幕文件名', '校验后英文字幕时长','校验后开始时间','校验后结束时间','校验后目标时长'])
        
        for (index, start_time, end_time, start_ms, end_ms, eng_text), (_, _, _, _, _, ch_text) in zip(eng_subs, ch_subs):
            duration_ms = end_ms - start_ms

            
            audio_file_name = combine_path_and_filename(csv_file,f'segment_{index-1}.mp3' ) # 根据序号动态生成音频文件名
            mp3duration_ms = get_mp3_duration_ms(audio_file_name)
            duration_difference = duration_ms - mp3duration_ms

            if (index==1):
                writer.writerow([index, start_time, end_time, duration_ms, eng_text, ch_text, audio_file_name, mp3duration_ms,duration_difference,'','',start_time,'',duration_ms])
            else:
                writer.writerow([index, start_time, end_time, duration_ms, eng_text, ch_text, audio_file_name, mp3duration_ms,duration_difference,'','','','',''])

# 示例用法


def calculate_wpm(text, duration_ms):
    """
    Calculate the words per minute (WPM) based on the given text and its duration in milliseconds.

    Parameters:
    text (str): The text to be spoken.
    duration_ms (int): The duration of the speech in milliseconds.

    Returns:
    tuple: Returns a tuple containing the number of words in the text and the words per minute (WPM).
    """
    # Calculate the number of words in the text
    word_count = len(text.split())

    # Convert duration to minutes
    duration_min = duration_ms / 60000

    # Calculate words per minute (WPM)
    wpm = word_count / duration_min

    return word_count, wpm

def estimate_duration_ms(text, wpm):
    """
    Estimate the duration of a recording in milliseconds based on the given text and words per minute (WPM).

    Parameters:
    text (str): The text to be spoken.
    wpm (float): The words per minute the text is spoken at.

    Returns:
    int: Estimated duration of the recording in milliseconds.
    """
    # Calculate the number of words in the text
    word_count = len(text.split())

    # Calculate duration in minutes
    duration_min = word_count / wpm

    # Convert duration to milliseconds
    duration_ms = int(duration_min * 60000)

    return word_count,duration_ms


'''
1. 根据中文生成英文字幕
2. 第一次生成英文语音
3. 如果英文语音时长和中文语音时长，差异超过500ms
4. 使用translate_text_to_englishV2方法，第二次生成英文字幕
5. 再次生成英文语音
6. 如果英文语音时长和中文语音时长，差异超过300ms，重复次数超过5次，则取得误差最小的一次
7. 继续开始翻译第二句英文字幕，字幕开始时长是第一次字幕的结束，重复上面的生成字幕的过程，最终误差不能超过500ms
继续重复上面的过程

'''


def adjust_translation_and_continue_chat(english_text, english_duration_ms, target_duration_ms, language_name,file_name,gptModel =GPTModel.GPT_4_o_MINI):
    """
    Adjusts the translation of text to fit a target duration and continues the chat with an additional message.
    Assumes that both translate_text_to_englishV3 and ContinueChat functions return a list of messages,
    and extracts the 'content' of the last message in the list.

    :param english_text: The text in English to be translated and adjusted.
    :param english_duration_ms: The duration of the original English text in milliseconds.
    :param target_duration_ms: The target duration in milliseconds for the adjusted text.
    :param language_name: The name of the language into which the text is being translated.
    :param additional_message: An additional message to continue the chat after the initial adjustment.
    :return: The 'content' of the last message in the adjusted message list.
    """
    # Translate and adjust the text based on the provided parameters

    
    #创建GPT翻译对象
    gptranslator = GPTTranslator()
    gptranslator.set_model(gptModel)
    
    
    message_list = gptranslator.translate_text_to_englishV3(english_text, english_duration_ms, target_duration_ms, language_name)
    SystemLogger.info(message_list)
    #取得校验的结果
    last_message_content= getcontentByMessageList(message_list)

    #记录所有的生成的英文字幕和声音文件和声音文件的时长
    attempts = []
    
     
    filePerfix=  getNumbersByFileName(file_name)
    fileDirectory =getDirectory(file_name)
    j=0
    _temp_fileindex = str(filePerfix)+"_"+str(j)
    audio_path = gptranslator.text_to_speechV3OpenAI(last_message_content, _temp_fileindex, fileDirectory)
    en_mp3duration_ms = get_mp3_duration_ms(audio_path)
    SystemLogger.info("===try=="+str(j)+"====")
    SystemLogger.info("last_message_content:",last_message_content)
    SystemLogger.info("en_mp3duration_ms:",en_mp3duration_ms)
    j=j+1

    attempts.append((last_message_content, audio_path, en_mp3duration_ms, abs(en_mp3duration_ms -target_duration_ms)))
 
    retry =False

    if (gptranslator.get_model() == GPTModel.GPT_3_5_TURBO.value):
        x=10
    else:
       x=5
    for i in range(0, x):
        if abs(en_mp3duration_ms -target_duration_ms) >360:
            retry=False
            if en_mp3duration_ms>target_duration_ms :
            #如果时长太长了，则执行下面的
                message_List= gptranslator.ContinueChat(message_list,f"这个{language_name}字幕太长了")
                SystemLogger.info(f"这个{language_name}字幕太长了")

                last_message_content= getcontentByMessageList(message_list)

                #我只需要调整后的结果，如果出现了中文或者“Adjusted subtitle”
                message_List= gptranslator.ContinueChat(message_list,f"请直接输出结果")
                SystemLogger.info(f"请直接输出结果")
                last_message_content= getcontentByMessageList(message_list)

                #如果最后的结果全是中文，则跳出重做一次
                retry= gptranslator.contains_chinese(last_message_content)
                if (retry == True):
                    SystemLogger.info(f"最后的结果全是中文，则跳出重做一次")
                    break

                audio_path = gptranslator.text_to_speechV3OpenAI(last_message_content, str(filePerfix)+"_"+str(j), fileDirectory)
                en_mp3duration_ms = get_mp3_duration_ms(audio_path)
                SystemLogger.info("===try=="+str(j)+"====")
                SystemLogger.info("last_message_content:",last_message_content)
                SystemLogger.info("en_mp3duration_ms:",en_mp3duration_ms)
                j=j+1
                attempts.append((last_message_content, audio_path, en_mp3duration_ms, abs(en_mp3duration_ms -target_duration_ms)))

            else:  
            #如果时长太短了，则执行下面的
                message_list= gptranslator.ContinueChat(message_list,f"这个{language_name}字幕太短了")
                SystemLogger.info(f"这个{language_name}字幕太短了")

                #我只需要调整后的结果，如果出现了中文或者“Adjusted subtitle”
                message_List= gptranslator.ContinueChat(message_list,f"请直接输出结果")
                SystemLogger.info(f"请直接输出结果")
                last_message_content= getcontentByMessageList(message_list)
                if (retry == True):
                    SystemLogger.info(f"最后的结果全是中文，则跳出重做一次")
                    break
                #如果最后的结果全是中文，则跳出重做一次
                retry= gptranslator.contains_chinese(last_message_content)
                if (retry == True):
                    break
                
                last_message_content= getcontentByMessageList(message_list)
                audio_path = gptranslator.text_to_speechV3OpenAI(last_message_content, str(filePerfix)+"_"+str(j), fileDirectory)
                en_mp3duration_ms = get_mp3_duration_ms(audio_path)
                SystemLogger.info("===try=="+str(j)+"====")
                SystemLogger.info("last_message_content:",last_message_content)
                SystemLogger.info("en_mp3duration_ms:",en_mp3duration_ms)
                j=j+1

                attempts.append((last_message_content, audio_path, en_mp3duration_ms, abs(en_mp3duration_ms -target_duration_ms)))
            
            if(i==9):
                if (target_duration_ms<0):
                    break
            '''                
            if(i==9):
                SystemLogger.info("重试了9次了,需要改成gpt4")
                retry=True
            '''

        else:
            break


    if (retry ==True):
       #attempts= adjust_translation_and_continue_chat(english_text, english_duration_ms, target_duration_ms, language_name,file_name,GPTModel.GPT_4_TURBO_2024_04_09)
       attempts= adjust_translation_and_continue_chat(english_text, english_duration_ms, target_duration_ms, language_name,file_name,GPTModel.GPT_4_o_MINI)
       return attempts
    
    SystemLogger.info(attempts)
    best_attempt = min(attempts, key=lambda x: x[3])

    return best_attempt[:3] 

def getcontentByMessageList(message_List):
    if message_List and isinstance(message_List[-1], dict):
        last_message_content = message_List[-1].get('content', '')
    else:
        last_message_content = ""
    return last_message_content

def getNumbersByFileName(filename):

    directory_path, _filename = os.path.split(filename)

    # 分割字符串
    parts = _filename.split('_')
    # 进一步分割以获取数字
    number_part = parts[1].split('.')[0]
    SystemLogger.info(number_part)
    return number_part

def update_csv_with_adjustmentsV1(csv_file):
    # 读取CSV文件中的数据
    rows = []
    with open(csv_file, 'r', newline='', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        headers = next(reader)  # 读取表头
        for row in reader:
            rows.append(row)
    
    # 对每一行进行校验和调整
    adjusted_rows = []
    for row in rows:
        '''
        0'序号', 
        1'开始时间',
        2'结束时间', 
        3'时长(ms)', 
        4'英文字幕', 
        5'中文字幕', 
        6'生成的音频文件名', 
        7'音频文件时长', 
        8'时长差',
        9'校验后英文字幕',
        10'校验后英文字幕文件名',
        11'校验后英文字幕时长',
        12'校验后开始时间',
        13'校验后结束时间',
        14'校验后目标时长'
        '''

        english_text = row[4]  # 假设英文字幕在第5列
        english_duration_ms =  int(row[7])# 假设时长(ms)在第4列
        # 假设目标时长需要根据其他逻辑计算或者是固定值
        target_duration_ms = int(row[14])   # 示例固定值
        language_name = "英文"
        file_name = row[6]  # 假设音频文件名在第7列

        #校验后开始时间 = 前面一行的校验后的结束时间,如果是第一行则="开始时间"，如果除第一行外，校验后的开始时间=上一行的校验后的结束时间
        #校验后的目标时长=结束时间-校验后开始时间

        last_message_content, audio_path, en_mp3duration_ms = adjust_translation_and_continue_chat(english_text, english_duration_ms, target_duration_ms, language_name, file_name)
        # 更新行数据，这里需要根据你的具体需求来调整列的索引
        row[9] = last_message_content  # 校验后英文字幕
        row[10] = audio_path  # 校验后英文字幕文件名
        row[11] = en_mp3duration_ms  # 校验后英文字幕时长
       
        #校验后的结束时间=校验后开始时间+校验后英文字幕时长
        

        adjusted_rows.append(row)
     

    # 将更新后的数据写回CSV文件
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(headers)  # 写入表头
        writer.writerows(adjusted_rows)  # 写入更新后的数据



'''
输出最合适长度的语句
#继续聊天
english_text = "This is a high-definition cable for computers and TVs"
english_duration_ms = 3192
target_duration_ms=2280
languagename="英文"
filename ="segment_1.mp3"
last_message_content,audio_path,en_mp3duration_ms= adjust_translation_and_continue_chat(english_text, english_duration_ms, target_duration_ms, languagename,filename)
SystemLogger.info(last_message_content,audio_path,en_mp3duration_ms)
'''



def time_str_to_ms(time_str):
    # 将时间字符串转换为毫秒
    dt = datetime.strptime(time_str, "%H:%M:%S,%f")
    return (dt.hour * 3600 + dt.minute * 60 + dt.second) * 1000 + dt.microsecond // 1000

def ms_to_time_str(ms):
    # 将毫秒转换回时间字符串
    seconds, ms = divmod(ms, 1000)
    hours, seconds = divmod(seconds, 3600)
    minutes, seconds = divmod(seconds, 60)
    return f"{hours:02}:{minutes:02}:{seconds:02},{ms:03}"

def update_csv_with_adjustments(csv_file):
    rows = []
    with open(csv_file, 'r', newline='', encoding='utf-8-sig') as file:
        reader = csv.reader(file)
        headers = next(reader)
        for row in reader:
            rows.append(row)
    
    adjusted_rows = []
    for i, row in enumerate(rows):
        if i == 0:
            start_time_ms = time_str_to_ms(row[1])  # 对于第一行，使用原始的开始时间
            target_duration_ms = time_str_to_ms(row[2])
        else:
            start_time_ms = time_str_to_ms(row[1]) if i == 0 else time_str_to_ms(adjusted_rows[-1][13])  # 使用上一行的校验后结束时间作为这一行的开始时间
                # 校验后的目标时长=结束时间-校验后开始时间
            target_duration_ms = time_str_to_ms(row[2])  - start_time_ms

        english_text = row[4]
        english_duration_ms = int(row[7])
        #target_duration_ms = int(row[14])

        file_name = row[6]
        
        last_message_content, audio_path, en_mp3duration_ms = adjust_translation_and_continue_chat(english_text, english_duration_ms, target_duration_ms, "英文", file_name)

        adjusted_start_time_ms = start_time_ms  # 校验后的开始时间
        adjusted_end_time_ms = start_time_ms + en_mp3duration_ms  # 校验后的结束时间

        '''
        0'序号', 
        1'开始时间',
        2'结束时间', 
        3'时长(ms)', 
        4'英文字幕', 
        5'中文字幕', 
        6'生成的音频文件名', 
        7'音频文件时长', 
        8'时长差',
        9'校验后英文字幕',
        10'校验后英文字幕文件名',
        11'校验后英文字幕时长',
        12'校验后开始时间',
        13'校验后结束时间',
        14'校验后目标时长'
        '''

        row[9] = last_message_content
        row[10] = audio_path
        row[11] = str(en_mp3duration_ms)
        row[12] = ms_to_time_str(adjusted_start_time_ms)
        row[13] = ms_to_time_str(adjusted_end_time_ms)
        
        adjusted_rows.append(row)
    
    with open(csv_file, 'w', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file)
        writer.writerow(headers)
        writer.writerows(adjusted_rows)
   



def update_csv_with_adjustmentsV3(csv_file,languagename):
    #new_csv_file = "adjust_"+csv_file
    new_csv_file = add_prefix_to_filename(csv_file, 'adjust_')

    with open(csv_file, 'r', newline='', encoding='utf-8-sig') as read_file, open(new_csv_file, 'w', newline='', encoding='utf-8-sig') as write_file:
        reader = csv.reader(read_file)
        writer = csv.writer(write_file)

        headers = next(reader)
        writer.writerow(headers)  # 写入表头

        previousEndTime =0
    
        for i, row in enumerate(reader):
            # 进行调整的逻辑
            # 示例逻辑，根据实际情况修改
            if i == 0:
                start_time_ms = time_str_to_ms(row[1])
            else:
                # 使用上一行的校验后结束时间作为这一行的开始时间
                start_time_ms = time_str_to_ms(previousEndTime)
            
            # 校验后的目标时长=结束时间-校验后开始时间
            target_duration_ms = time_str_to_ms(row[2]) - start_time_ms
            #序号,开始时间,结束时间,时长(ms),英文字幕,中文字幕,生成的音频文件名,音频文件时长,时长差,校验后英文字幕,校验后英文字幕文件名,校验后英文字幕时长,校验后开始时间,校验后结束时间,校验后目标时长
            #def adjust_translation_and_continue_chat(english_text, english_duration_ms, target_duration_ms, language_name,file_name):
            #英文mp3文件的时长

            #如果英文字幕是空字符，直接算出空字符需要的时长，填充到表格中
            if str(row[4]).strip() != "":
                
                en_mp3duration_ms =int(row[7])
                #如果原生成的音频文件的时长已经符合要求了，则不需要再重新生成
                if abs(en_mp3duration_ms -target_duration_ms) <=360:
                    last_message_content= row[4]
                    audio_path =row[6]
                    en_mp3duration_ms =int(row[7]) 
                else:
                    last_message_content, audio_path, en_mp3duration_ms = adjust_translation_and_continue_chat(row[4], int(row[7]), target_duration_ms, languagename, row[6])
                
                # 更新行数据
                row[9] = last_message_content
                row[10] = audio_path
                row[11] = str(en_mp3duration_ms)
                row[12] = ms_to_time_str(start_time_ms)
                row[13] = ms_to_time_str(start_time_ms + en_mp3duration_ms)
                
                previousEndTime=ms_to_time_str(start_time_ms + en_mp3duration_ms)
                
                writer.writerow(row)  # 写入更新后的行
                write_file.flush()  # 立即将数据写入文件
            else:
                segment_index=str(int(row[0])-1)+"_0"
                fileDirectory =getDirectory(csv_file)
                audio_file_path = os.path.join(fileDirectory, f"segment_{segment_index}.mp3")
                generate_silence(target_duration_ms,audio_file_path)
                SystemLogger.info(audio_file_path+"(生成空白声音)")
                # 更新行数据
                row[9] = " "
                row[10] = audio_file_path
                row[11] = str(target_duration_ms)
                row[12] = ms_to_time_str(start_time_ms)
                row[13] = ms_to_time_str(start_time_ms + target_duration_ms)
                
                previousEndTime=ms_to_time_str(start_time_ms + target_duration_ms)
                
                
                writer.writerow(row)  # 写入更新后的行
                write_file.flush()  # 立即将数据写入文件
    

    return new_csv_file

    # 用更新后的临时文件替换原始文件
    #shutil.move(temp_file.name, csv_file)

#取得校验后的mp3文件的列表
def extract_audio_paths_from_csv(csv_file):
    audio_paths = []  # 初始化一个空列表来存储音频文件路径

    with open(csv_file, 'r', newline='', encoding='utf-8-sig') as file:
        reader = csv.DictReader(file)  # 使用DictReader读取CSV，这样可以通过列名访问每个值

        for row in reader:
            audio_path = row['校验后英文字幕文件名']  # 获取“校验后英文字幕文件名”列的值
            if audio_path:  # 确保路径非空
                audio_paths.append(audio_path)  # 将路径添加到列表中

    return audio_paths

def csv_to_srt(csv_filename, srt_filename):
    with open(csv_filename, mode='r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        
        with open(srt_filename, mode='w', encoding='utf-8') as srt_file:
            # 逐行读取CSV文件，并将每行转换为SRT格式
            for i, row in enumerate(csv_reader, start=1):
                # 提取需要的字段
                start_time = row['校验后开始时间']
                end_time = row['校验后结束时间']
                subtitle = row['校验后英文字幕']
                
                # 将信息格式化为SRT格式并写入文件
                srt_file.write(f"{i}\n")
                srt_file.write(f"{start_time} --> {end_time}\n")
                srt_file.write(f"{subtitle}\n\n")
    return srt_filename
