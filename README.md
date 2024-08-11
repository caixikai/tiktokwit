
# Tiktokwit: Automated Video Translation Using LLM Agent Reflective Mechanism
<p align="center">
  <a href="./README.md">English</a> |
  <a href="./README_CN.md">Chinese</a> |
</p>

## Project Introduction
- This project utilizes the reflective mechanism of LLM Agent to control translation duration by verifying the translation results, achieving automatic synchronization and high-quality translation of audio and video.
- After testing, the project currently supports automatic translation from Chinese to English, French, Portuguese, Spanish, German, and Russian, as well as from English to French, Portuguese, Spanish, German, and Russian. Other languages have not been tested yet.

## Differences from Similar Projects
- Most current similar projects achieve synchronization by lengthening or shortening the audio and video, which can cause the audio to speed up or slow down inconsistently.
- This project uses the reflective mechanism of LLM Agent to verify the translation results and control the translation duration of each subtitle segment, ensuring that the duration discrepancy between the translated audio and video files does not exceed 300ms.

### Project Steps Explanation
1. **Convert Video to Audio**
   - Convert the video file to an MP3 audio file.
   - Upload the generated audio file and obtain its URL.
   - Record the path and URL of the generated MP3 file.

2. **Extract Background Sound from Audio**
   - Extract background sound from the converted audio file and generate a new MP3 file.
   - Record the path of the generated background sound MP3 file.

3. **Convert Audio to Subtitle File**
   - Convert the audio file to a Chinese subtitle file.
   - Detect the language of the subtitle file, and throw an exception if it matches the target language.
   - Check if the subtitle file is empty; if empty, return a failure.
   - Insert blank subtitles if needed.

4. **Translate Subtitle File**
   - Translate the Chinese subtitle file into the target language subtitle file.
   - Adjust blank character lines in the subtitle file.
   - Check if the number of Chinese and English subtitle paragraphs are consistent; retry up to 3 times if inconsistent.

5. **Generate Target Language Audio File**
   - Convert the target language subtitle file into an audio file.

6. **Verify Subtitle File**
   - Merge Chinese and English subtitle file information into a CSV file.
   - Verify the target language audio file based on the CSV file.
   - Merge the verified audio file.

7. **Merge Audio and Video**
   - Merge the target language audio file with the background sound video file to generate the final video file.

8. **Generate Final Subtitle File**
   - Generate the target language subtitle file based on the CSV file.

9. **Burn Subtitles and Video**
   - Burn the target language subtitles and video together to generate the final file with timestamps.

## Core Code Available
- The SaaS version of this project is now online at https://www.tiktokwit.com/mp4. Feel free to try it out.
- The current version is a relatively complete version, the result of efforts by alex.cai and WTWT.He over the past few months, with additional help from collaborator (xianyu) in building the commercial front-end interface.
- Thank you for your support of this project, and we hope more people can participate.

## Getting Started
### 1. Install Dependencies
Currently only supports running on Windows. For Mac and Linux, FFmpeg installation needs to be handled separately.
Refer to online installation steps for FFmpeg on Windows.

```sh
pip install -r requirements.txt
```

### 2. Configure Parameters in SysConfig File
Include parameters for various APIs of VolcEngine and OpenAI.

### 3. Run Run.py
```sh
python Run.py
```

## License

This repository follows the [Tiktokwit Open Source License](https://github.com/caixikai/tiktokwit/blob/main/LICENSE).

- Allowed to be used as a backend service directly for commercial purposes, but not allowed to provide SaaS services.
- Any form of commercial service without commercial authorization must retain relevant copyright information.

For full details, see [Tiktokwit Open Source License](https://github.com/caixikai/tiktokwit/blob/main/LICENSE).

Contact: caixikai01@gmail.com

## Extended Ideas
Here are some ideas we haven't had time to try yet but hope the open-source community can explore:

1. Try other LLMs. We mainly used gpt-4-o for prototyping. We hope others can try different LLMs to see how their translations perform. I have already tried GPT-3.5 and other LLMs, and the prompts may need further adjustment.
2. Consider making further modifications to this project's code with reference to Andrew Ng's translation-agent.
3. For Asian languages, the OpenAI output for Japanese and Korean audio files did not test well.

# Community Group
<img src="https://github.com/caixikai/tiktokwit/blob/main/weixin.png?raw=true" alt="WeChat Group QR Code" width="500">

# Video Demonstration
All demo videos are in the tiktokwit/demomp4/ directory.
