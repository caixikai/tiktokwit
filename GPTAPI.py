import os
import re
import time
import uuid
from ctypes import util
from distutils import config
from enum import Enum

import requests
from pydub import AudioSegment

import SysConfig
from Logger import SystemLogger
from util import generate_silence, getDirectory

import openai  # 确保已安装并正确配置了OpenAI库

# 定义一个名为GPTModel的枚举
class GPTModel(Enum):
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_4_o ="gpt-4o"

class GPTTranslator:
    def __init__(self, gpt_model=GPTModel.GPT_4_o):
        
        os.environ['OPENAI_API_KEY'] = SysConfig.OPENAI_API_KEY
        self.gpt4Model = gpt_model

    def set_model(self, model_version):
        if isinstance(model_version, GPTModel):
            self.gpt4Model = model_version
            SystemLogger.info(f'GPTTranslator gpt4Model is :{self.gpt4Model.value}')
            
        else:
            raise ValueError("Invalid GPT model version")

    def get_model(self):
        return self.gpt4Model.value



    def file_recognizeV2(self,appid, token, cluster, audio_url, language="es-MX", srt_filename="output.srt"):
        base_url = 'https://openspeech.bytedance.com/api/v1/vc'
        headers = {'Authorization': 'Bearer; {}'.format(token), 'Content-Type': 'application/json'}

        def submit_task():
            payload = {
                "url": audio_url,
            }
            params = dict(
                appid=appid,
                language=language,
                use_itn='True',
                use_capitalize='True',
                max_lines=1,
                words_per_line=46,
            )
            response = requests.post(f'{base_url}/submit', params=params, json=payload, headers=headers)
            if response.status_code != 200:
                raise Exception("Submission failed: " + response.text)
            return response.json()['id']

        def query_task(task_id):
            params = {
                'appid': appid,
                'id': task_id,
            }
            response = requests.get(f'{base_url}/query', params=params, headers=headers)
            if response.status_code != 200:
                raise Exception("Query failed: " + response.text)
            return response.json()

        task_id = submit_task()
        start_time = time.time()
        while True:
            time.sleep(2)
            resp = query_task(task_id)
            SystemLogger.info(resp.get('message') )
            if resp.get('message') == 'Success':  # Assuming 'finished' status indicates completion
                SystemLogger.info("success")
                return self.generate_srt(resp, srt_filename)
            if time.time() - start_time > 300:  # wait time exceeds 300s
                SystemLogger.info('wait time exceeds 300s')
                break

    def format_time(self,ms):
        """Convert milliseconds to SRT subtitle format."""
        hours, ms = divmod(ms, 3600000)
        minutes, ms = divmod(ms, 60000)
        seconds, ms = divmod(ms, 1000)
        return f'{int(hours):02}:{int(minutes):02}:{int(seconds):02},{int(ms):03}'

    def generate_srt(self,resp, srt_filename):
        utterances = resp['utterances']
        with open(srt_filename, 'w', encoding='utf-8') as f:
            for i, utterance in enumerate(utterances, start=1):
                start_time = self.format_time(utterance['start_time'])
                end_time = self.format_time(utterance['end_time'])
                text = utterance['text']
                f.write(f'{i}\n')
                f.write(f'{start_time} --> {end_time}\n')
                f.write(f'{text}\n\n')
        return srt_filename
    #2.===============================================================================

    #3.中文字幕变成英文字幕=============================================================
    def translate_subtitles_to_english(self,chinese_subtitles_file,source_language_name,languagename):

        # 读取中文字幕文件内容
        with open(chinese_subtitles_file, 'r', encoding='utf-8') as file:
            chinese_subtitles = file.read()

        # 输入您想要对话的文本
        user_input = f"我想把下面的{source_language_name}字幕翻译成{languagename}字幕，并帮我直接输出成{languagename}字幕格式(不要改变序号)，请直接输出srt文件的内容，{source_language_name}字幕内容如下:\n" + chinese_subtitles

        # 调用 GPT-3.5 Turbo 模型
        client = openai.OpenAI()

        # 设置超时时间为60秒
        timeout_seconds = 3000

        print(user_input)
        message_list  =[
            {"role": "system", "content":f"你是一个字幕翻译助手，可以帮我把{source_language_name}字幕翻译成{languagename}字幕"},
            {"role": "user", "content": user_input},
        ]
        
        response = client.chat.completions.create(
            model=self.get_model(),
            messages=message_list,
            timeout=timeout_seconds
        )

        # 提取生成的回复
        chat_response = response.choices[0].message.content


        # 提取生成的回复
        new_user_message = {"role": "system", "content": chat_response}

        message_list.append(new_user_message)

        #格式化只输出英文字符
        new_message= f"请直接输出srt文件的最终版本，不需要任何解释和其他信息"

        message_list= self.ContinueChat(message_list,new_message)

        #取得最后一个内容
        if message_list and isinstance(message_list[-1], dict):
            last_message_content = message_list[-1].get('content', '')
        else:
            last_message_content = ""

        # 将英文字幕写入文件
        english_subtitles_file = chinese_subtitles_file.replace('.srt', '_english.srt')
        with open(english_subtitles_file, 'w', encoding='utf-8') as file:
            file.write(last_message_content)

        self.remove_lines_with_backticks(english_subtitles_file)

        return english_subtitles_file

    def remove_lines_with_backticks(self,file_path):
        """
        读取指定的SRT文件，移除包含反引号字符的整行，并将结果保存到一个新的文件中。

        参数:
        file_path (str): 输入SRT文件的路径。

        返回:
        无。清理后的文件将保存为 'cleaned_' + 原始文件名。
        """
        
        SystemLogger.info("清理不符合规则的行数据")
        # 打开指定路径的文件，以只读模式读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()  # 读取文件的所有行

        # 创建一个列表，只保留不包含反引号字符的行
        cleaned_lines = [line for line in lines if '```' not in line]

        # 打开一个新文件，以写模式写入清理后的行
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(cleaned_lines)  # 写入清理后的行
        


    #去掉其中多余的中文和句子前后的"号
    def trim_subtitles_to_english(self,english_subtitles,languagename="英文"):

        if self.contains_chinese(english_subtitles) ==False:
            english_subtitles= english_subtitles.strip("\"").strip(" ")
            return english_subtitles

        # 输入您想要对话的文本
        user_input = "<"+english_subtitles+">能只返回其中的完整的"+languagename+"句子吗，不需要返回其他多余的信息或者回答,并去掉句子前后的“号"

        # 调用 GPT-3.5 Turbo 模型
        client = openai.OpenAI()

        # 设置超时时间为60秒
        timeout_seconds = 3000

        response = client.chat.completions.create(
            model=self.get_model(),
            messages=[
                {"role": "user", "content": user_input},
            ],
            timeout=timeout_seconds
        )

        # 提取生成的回复
        chat_response = response.choices[0].message.content
        
        return chat_response

    def translate_text_to_english(self,chinese_text,chinese_duration_ms,english_text,english_duration_ms,source_language_name,languagename):
        # 输入您想要对话的文本
        client = openai.OpenAI()
        # 设置超时时间为60秒
        timeout_seconds = 3000
        #gpt-4-1106-preview
        #
        str_chinese_duration_ms= str(chinese_duration_ms)
        str_english_duration_ms=str(english_duration_ms)

        response = client.chat.completions.create(
            model=self.get_model(),
            messages=[
                {"role": "system", "content": "你是一个字幕翻译助手"},
                #{"role": "user", "content": "尽量保证从中文翻译成"+languagename+"，两段语音时长保持一致和内容也要保持一致,中文字幕是<"+chinese_text+">, 中文语音的文件时长是"+str(chinese_duration_ms)+"ms。英文字幕是<"+english_text+">, 英文语音的文件时长是"+str(english_duration_ms)+"ms。帮我重新翻译英文字幕，并达到我的要求，请直接输出推荐的英文句子，不用解释"},
                {"role": "user", "content": f"尽量保证从{source_language_name}翻译成{languagename}，两段语音时长保持一致和内容也要保持一致,\n{source_language_name}字幕是<{chinese_text}>, {source_language_name}语音的文件时长是{str_chinese_duration_ms}ms。\n{languagename}字幕是<{english_text}>, {languagename}语音的文件时长是{str_english_duration_ms}ms。\n帮我重新翻译{languagename}字幕，并达到我的要求，请直接输出推荐的英文句子，不用解释"},

            ],
            timeout=timeout_seconds
        )

        # 提取生成的回复
        chat_response = response.choices[0].message.content

        
        return chat_response

    #3.===============================================================================


    def translate_text_to_englishV2(self,english_text,english_duration_ms,target_duration_ms,languagename):
        prompt_text = f"""
        角色：字幕调整专家

        背景：该角色专门从事优化视频内容的字幕，使之适应不同的播放时长和观众阅读速度。具备深厚的语言学知识，对语速、信息密度和观众理解能力有深入的理解。

        注意事项：聚焦于改写和调整字幕时长，确保其既忠实于原文意义，又能在给定的时间内舒适地被观众阅读。

        简介：

        作者: cxk
        版本: 1.3
        语言: 中文
        描述: 本模板旨在生成高效、精确的{languagename}字幕调整指导，帮助内容创作者和字幕作者优化字幕长度和表达，以适应不同的播放时长需求。
        技能：

        - 能够快速识别并提取关键信息。
        - 精通简化和重构句子，同时保持原始意义不变。
        - 熟悉多种语言风格和表达方式，能够根据内容类型和目标观众调整字幕风格。

        目标：

        - 简化或扩展原有字幕，以适应特定的播放时长。
        - 优化字幕的阅读流畅度，确保观众能够在限定时间内理解内容。
        - 提高字幕的整体质量，增强观众的观看体验。

        限制：

        - 必须保持字幕的原始意图和准确性。
        - 调整后的字幕时长需严格符合目标时长要求。
        - 调整过程中需考虑到字幕的语言习惯和文化差异。
        - 只返回调整后的字幕，不用返回思考的过程

        建议：

        - 在可能的情况下，使用同义词替换长单词或短语。
        - 考虑整合或分割信息，以更有效地利用空间和时间。
        - 对于复杂的调整需求，建议进行多轮修订和测试，确保最终结果的可读性和效果。

        要创建适合特定时长的{languagename}字幕提示词，你可以考虑以下几个策略：

        - **简化或扩展词汇**：如果需要缩短句子以适应更短的时长，尝试使用更简洁的词汇或短语替换长句子中的部分。相反，如果需要延长句子，可以添加描述性短语或细节来丰富内容。
        - **调整语速感知**：通过添加停顿（如逗号、破折号等）来人为地减慢语速感知，或通过减少这些停顿使语速感觉更快。
        - **利用同义词和近义词**：替换原句中的词汇，选用字数更多或更少的同义词，以调整句子长度。
        - **分割或合并句子**：根据需要调整的时长，可以将长句子分割成几个短句，或者相反，将几个短句合并为一个较长的句子。
        - **重构句子结构**：通过改变句子的结构来适应时长需求，比如从被动语态改为主动语态（或反之），这通常会影响句子的长度。

        初始化：
        为启动这个过程，请提供以下信息：

        - 需要调整的原始字幕文本。
        - 原始字幕对应的时长（毫秒）。
        - 目标字幕的期望时长（毫秒）。
        - 任何特定的风格或语言要求。
        - 只输出调整后的字幕，不用返回思考的过程。
        """

        # 原始英文字幕文本
        #original_subtitle = "This is a high-definition cable for computers and TVs"

        # 原始字幕对应的时长（毫秒）
        #original_duration_ms = 3192

        # 目标字幕的期望时长（毫秒）
        #target_duration_ms = 2280

        # 使用变量来构建上下文文本
        change_context = f"""
        {languagename}：{english_text}
        时长：{english_duration_ms}ms
        目标时长：{target_duration_ms}ms"""

        # 输入您想要对话的文本
        client = openai.OpenAI()
        # 设置超时时间为60秒
        timeout_seconds = 3000

        response = client.chat.completions.create(
            model=self.get_model(),
            messages=[
                {"role": "system", "content":prompt_text},
                {"role": "user", "content": change_context},

            ],
            timeout=timeout_seconds
        )

        # 提取生成的回复
        chat_response = response.choices[0].message.content

        
        return chat_response

    def translate_text_to_englishV3(self,english_text,english_duration_ms,target_duration_ms,languagename,max_retries=10):
        prompt_text = f"""
        角色：字幕调整专家

        背景：该角色专门从事优化视频内容的字幕，使之适应不同的播放时长和观众阅读速度。具备深厚的语言学知识，对语速、信息密度和观众理解能力有深入的理解。

        注意事项：聚焦于改写和调整字幕时长，确保其既忠实于原文意义，又能在给定的时间内舒适地被观众阅读。

        简介：

        作者: cxk
        版本: 1.3
        语言: 中文
        描述: 本模板旨在生成高效、精确的{languagename}字幕调整指导，帮助内容创作者和字幕作者优化字幕长度和表达，以适应不同的播放时长需求。
        技能：

        - 能够快速识别并提取关键信息。
        - 精通简化和重构句子，同时保持原始意义不变。
        - 熟悉多种语言风格和表达方式，能够根据内容类型和目标观众调整字幕风格。

        目标：

        - 简化或扩展原有字幕，以适应特定的播放时长。
        - 优化字幕的阅读流畅度，确保观众能够在限定时间内理解内容。
        - 提高字幕的整体质量，增强观众的观看体验。

        限制：

        - 必须保持字幕的原始意图和准确性。
        - 调整后的字幕时长需严格符合目标时长要求。
        - 调整过程中需考虑到字幕的语言习惯和文化差异。
        - 只返回调整后的字幕，不用返回思考的过程

        建议：

        - 在可能的情况下，使用同义词替换长单词或短语。
        - 考虑整合或分割信息，以更有效地利用空间和时间。
        - 对于复杂的调整需求，建议进行多轮修订和测试，确保最终结果的可读性和效果。

        要创建适合特定时长的{languagename}字幕提示词，你可以考虑以下几个策略：

        - **简化或扩展词汇**：如果需要缩短句子以适应更短的时长，尝试使用更简洁的词汇或短语替换长句子中的部分。相反，如果需要延长句子，可以添加描述性短语或细节来丰富内容。
        - **调整语速感知**：通过添加停顿（如逗号、破折号等）来人为地减慢语速感知，或通过减少这些停顿使语速感觉更快。
        - **利用同义词和近义词**：替换原句中的词汇，选用字数更多或更少的同义词，以调整句子长度。
        - **分割或合并句子**：根据需要调整的时长，可以将长句子分割成几个短句，或者相反，将几个短句合并为一个较长的句子。
        - **重构句子结构**：通过改变句子的结构来适应时长需求，比如从被动语态改为主动语态（或反之），这通常会影响句子的长度。

        初始化：
        为启动这个过程，请提供以下信息：

        - 需要调整的原始字幕文本。
        - 原始字幕对应的时长（毫秒）。
        - 目标字幕的期望时长（毫秒）。
        - 任何特定的风格或语言要求。
        - 只输出调整后的字幕，不用返回思考的过程。
        """

        # 原始英文字幕文本
        #original_subtitle = "This is a high-definition cable for computers and TVs"

        # 原始字幕对应的时长（毫秒）
        #original_duration_ms = 3192

        # 目标字幕的期望时长（毫秒）
        #target_duration_ms = 2280

        # 使用变量来构建上下文文本
        change_context = f"""
        {languagename}：{english_text}
        时长：{english_duration_ms}ms
        目标时长：{target_duration_ms}ms"""

        # 输入您想要对话的文本
        client = openai.OpenAI()
        # 设置超时时间为60秒
        timeout_seconds = 3000

        message_list  =[
                {"role": "system", "content":prompt_text},
                {"role": "user", "content": change_context},

            ]
        
        retries = 0
        while retries < max_retries:
            try:
                response = client.chat.completions.create(
                    model=self.get_model(),
                    messages=message_list,
                    timeout=timeout_seconds
                )
                # 提取生成的回复
                chat_response = response.choices[0].message.content
                chat_response = self.trim_subtitles_to_english(chat_response,languagename)
                break  # 如果调用成功，则退出循环
            except Exception as e:
                SystemLogger.info(f"An error occurred: {e}. Retrying in 10 seconds...")
                time.sleep(10)  # 出现异常后等待10秒
                retries += 1  # 重试次数加1



        # 提取生成的回复

        new_user_message = {"role": "system", "content": chat_response}

        message_list.append(new_user_message)

        #格式化只输出英文字符
        new_message= f"请直接输出调整后的{languagename}最终版本，不需要任何解释和其他信息"

        message_list= self.ContinueChat(message_list,new_message)
        
        return message_list

    import re



    def contains_chinese(self,text):
        """
        检查文本中是否包含中文字符。

        :param text: 需要检查的字符串
        :return: 如果字符串包含中文字符，则返回True；否则返回False。
        """
        # 使用正则表达式匹配中文字符的Unicode范围
        if re.search(r'[\u4e00-\u9fff]+', text):
            return True
        return False


    def ContinueChat(self,message_list, new_message, max_retries=10):
        retries = 0
        new_user_message = {"role": "user", "content": new_message}
        message_list.append(new_user_message)
        
        while retries < max_retries:
            try:
                # 只在这个调用周围放置try-except
                client = openai.OpenAI()  # 初始化客户端，根据你的设置进行调整
                timeout_seconds = 3000

                response = client.chat.completions.create(
                    model=self.get_model(),
                    messages=message_list,
                    timeout=timeout_seconds
                )

                # 提取生成的回复
                chat_response = response.choices[0].message.content

                chat_response = self.trim_subtitles_to_english(chat_response)

                break  # 如果调用成功，则退出循环
            except Exception as e:
                SystemLogger.info(f"An error occurred: {e}. Retrying in 10 seconds...")
                time.sleep(10)  # 出现异常后等待10秒
                retries += 1  # 重试次数加1

        if retries == max_retries:
            # 如果重试次数达到最大值仍未成功
            SystemLogger.info("Failed to get completion after retries. Returning current message list without system response.")
        else:
            # 如果成功，添加系统回复到消息列表

            new_system_message = {"role": "system", "content": chat_response}
            message_list.append(new_system_message)

        return message_list



    #4.英文的字幕文件变成英文的语音,并合成为最终的英文mp3文件==============================
    def text_to_speechV3OpenAI(self,text, segment_index, output_dir):
        """
        使用 OpenAI 的 TTS API 将文本转换为语音，并保存为音频文件。
        
        参数:
        - text: 要转换的文本。
        - segment_index: 音频片段的索引，用于生成音频文件的名称。
        - output_dir: 输出目录路径。
        
        返回:
        - audio_file_path: 生成的音频文件路径。
        """
        # 实例化 OpenAI 客户端
        client = openai.OpenAI()
    
        # 使用指定的参数调用 audio.speech.create 方法生成语音
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text,  # 使用函数参数中的文本
        )
        
        # 构造输出文件名
        audio_file_path = os.path.join(output_dir, f"segment_{segment_index}.mp3")
        
        # 将生成的语音流保存到文件
        response.stream_to_file(audio_file_path)
        
        return audio_file_path

    def parse_srt(self,srt_file):
        """
        解析 SRT 字幕文件，提取文本片段。
        
        参数:
        - srt_file: SRT 字幕文件路径。
        
        返回:
        - segments: 字幕文本片段列表。
        """
        with open(srt_file, 'r') as file:
            srt_content = file.read() + '\n\n'
        
        pattern = re.compile(r'\d+\n(\d{2}:\d{2}:\d{2},\d{3}) --> (\d{2}:\d{2}:\d{2},\d{3})\n(.*?)\n\n', re.DOTALL)
        matches = pattern.findall(srt_content)
        
        segments = []
        for start, end, text in matches:
                text = text.replace('\n', ' ').strip()  # 去除文本中的换行符和多余的空白字符
                if text == "":
                    text = "  "  # 如果文本为空，则添加占位符
                segments.append({'start': start, 'end': end, 'text': text})
        
        return segments

    def merge_audio_segments(self,segment_paths, output_mp3filename):
        """
        合并音频片段文件，并保存合并后的音频文件。
        
        参数:
        - segment_paths: 音频片段文件路径列表。
        - output_dir: 输出目录路径。
        
        返回:
        - merged_audio_file_path: 合并后的音频文件路径。
        """
        combined = AudioSegment.empty()
        for path in segment_paths:
            audio = AudioSegment.from_file(path)
            combined += audio
        
        # 构造输出文件路径
        #merged_audio_file_path = os.path.join(output_dir, output_mp3filename)

        # 导出合并后的音频文件
        combined.export(output_mp3filename, format="mp3")
        
        return output_mp3filename

    def srt_to_audio(self,english_srt_file,output_mp3filename):
        """
        主函数，用于生成音频文件并合并成一个音频文件。
        
        参数:
        - english_srt_file: 英文 SRT 字幕文件路径。
        
        返回:
        - merged_audio_file_path: 合并后的音频文件路径。
        """
        # 解析英文字幕文件
        segments = self.parse_srt(english_srt_file)
        
        # 输出目录为英文字幕文件所在目录
        output_dir = os.path.dirname(english_srt_file)
        
        audio_paths = []
        for i, segment in enumerate(segments):
            # 生成音频文件并保存
            print(segment['text'])
            if str(segment['text']).strip() != "":
                audio_path = self.text_to_speechV3OpenAI(segment['text'], i, output_dir)
                audio_paths.append(audio_path)
                SystemLogger.info(audio_path)
            else:
                #声音文件名
                segment_index=str(i)
                fileDirectory =getDirectory(english_srt_file)
                audio_path = os.path.join(fileDirectory, f"segment_{segment_index}.mp3")
                generate_silence(1000,audio_path)
                audio_paths.append(audio_path)
                SystemLogger.info(audio_path+"(空白声音)")

        # 合并音频文件
        #cxkk
        merged_audio_file_path = self.merge_audio_segments(audio_paths, output_mp3filename)
        
        return merged_audio_file_path
    #4.===============================================================================



if __name__ == "__main__":
    

    text ="中文翻译: is very good"   
    gptranslator = GPTTranslator()
    print(gptranslator.get_model())

    result = gptranslator.trim_subtitles_to_english(text)
    print(result)

    gptranslator.set_model(GPTModel.GPT_4_TURBO_2024_04_09)
    print(gptranslator.get_model())

    result = gptranslator.trim_subtitles_to_english(text)
    print(result)
    
