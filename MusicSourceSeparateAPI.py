import base64
import json
import logging
import requests
import time
from VolcengineToken import volcengine_get_Token



def invoke_sami_http_service(audio_path, token, model, output_file):
    """
    Invoke SAMI HTTP service to process the audio file.

    Args:
        audio_path (str): Path to the audio file.
        token (str): Authentication token.
        model (str): Model parameter.
        output_file (str): Path to the output file for separated background audio.

    Returns:
        str: Path to the output file with separated background audio.
    """
    # Constants
    domain = "https://sami.bytedance.com"

    # Auth token
    appkey = 'fKwJnydFXh'
    # SAMI method
    version = "v4"
    namespace = "MusicSourceSeparate"

    payload_output_file = "output.json"
    is_dump = True

    # Construct HTTP request
    # 1. Read local audio file
    try:
        with open(audio_path, "rb") as audio_file:
            content = audio_file.read()
    except IOError as e:
        logging.error(f"Failed to read file: {e}")
        return None

    data = base64.b64encode(content).decode("utf-8")
    body = {
        "data": data,
        "payload": json.dumps({"model": model})
    }
    url_path = f"{domain}/api/v1/invoke?version={version}&token={token}&appkey={appkey}&namespace={namespace}"
    logging.info(f"Invoke request: {url_path}")

    # HTTP POST request
    start_time = time.time()
    try:
        response = requests.post(url_path, json=body)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logging.error(f"HTTP request failed: {e}")
        return None
    logging.info(f"HTTP invoke: cost={int((time.time() - start_time) * 1000)}ms")

    # Parse HTTP response
    ret = response.content
    if response.status_code != 200:
        logging.error(f"Request failed: {ret.decode('utf-8')}")
        return None

    try:
        sami_resp = response.json()
    except json.JSONDecodeError as e:
        logging.error(f"Parse response failed: {ret.decode('utf-8')}, {e}")
        return None

    payload_str = sami_resp.get("payload", "")
    logging.info(f"Response task_id={sami_resp['task_id']}, payload={payload_str}, data=[{len(sami_resp.get('data', b''))}]byte")

    if is_dump and payload_str:
        with open(payload_output_file, "w") as f:
            f.write(payload_str)

    if is_dump and 'data' in sami_resp:
        with open(output_file, "wb") as f:
            f.write(base64.b64decode(sami_resp['data']))

    return output_file

def separate_background_audio(audio_path, output_file):
    """
    Process the given audio file and return the path to the separated background audio file.

    Args:
        audio_path (str): Path to the input audio file.
        output_file (str): Path to the output file for separated background audio.

    Returns:
        str: Path to the output background audio file.
    """
    token = volcengine_get_Token()
    model = "2track_acc"
    output_path = invoke_sami_http_service(audio_path, token, model, output_file)
    return output_path

if __name__ == "__main__":
    audio_path = "0420.mp3"
    output_file = "0420_output_background.mp3"
    output_path = separate_background_audio(audio_path, output_file)
    print(f"Separated background audio saved to: {output_path}")
