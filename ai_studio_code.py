# To run this code you need to install the following dependencies:
# pip install google-genai

import mimetypes
import os
import re
import struct
from google import genai
from google.genai import types


def save_binary_file(file_name, data):
    f = open(file_name, "wb")
    f.write(data)
    f.close()
    print(f"File saved to to: {file_name}")


def generate():
    client = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )

    model = "gemini-2.5-flash-preview-tts"
    contents = [
        types.Content(
            role="user",
            parts=[
                types.Part.from_text(text="""Read the following transcript based on the audio profile.

# Audio Profile
The calm clear teaching voice of a Buddhist monk.

## Scene:
A quiet buddhist temple.

## Transcript:
ศีล 5: รากฐานของจริยธรรมและสันติสุขในสังคมไทย
ในพระพุทธศาสนา \"ศีล 5\" (The Five Precepts) ถือเป็นข้อปฏิบัติพื้นฐานที่สำคัญที่สุดสำหรับ \"ฆราวาส\" (laypeople) หรือบุคคลทั่วไป ศีลไม่ได้ถูกมองว่าเป็นกฎหมายที่บังคับให้คนต้องทำตามอย่างเคร่งครัด แต่เป็นข้อพึงระวังเพื่อฝึกฝนตนเองให้มีสติและไม่ \"เบียดเบียน\" (to exploit/harm) ผู้อื่น ซึ่งเป็นรากฐานของการอยู่ร่วมกันอย่างสงบสุข

ข้อที่ 1 ปาณาติบาต (ละเว้นจากการฆ่าสัตว์): ไม่เพียงแต่หมายถึงการไม่ทำลายชีวิตเท่านั้น แต่ยังครอบคลุมถึงการไม่ทำร้ายผู้อื่น คนไทยมักเชื่อมโยงข้อนี้กับการปลูกฝังความ \"เมตตากรุณา\" (compassion) ต่อเพื่อนมนุษย์และสัตว์โลก

ข้อที่ 2 อทินนาทาน (ละเว้นจากการลักทรัพย์): คือการเคารพในสิทธิและทรัพย์สินของผู้อื่น ไม่เอาของที่เจ้าของไม่ได้อนุญาตมาเป็นของตน ซึ่งเป็นการสร้างความไว้วางใจในชุมชน

ข้อที่ 3 กาเมสุมิจฉาจาร (ละเว้นจากการประพฤติผิดในกาม): เน้นย้ำถึงความซื่อสัตย์ต่อคู่ครองและการให้เกียรติครอบครัวของผู้อื่น เพื่อป้องกันปัญหาความ \"ร้าวฉาน\" (rift/brokenness) ในครอบครัว

ข้อที่ 4 มุสาวาท (ละเว้นจากการพูดปด): การไม่พูดโกหก ไม่พูดคำหยาบ และไม่พูดนินทา ข้อนี้มีความสำคัญมากในการสร้างความสัมพันธ์ที่จริงใจ

ข้อที่ 5 สุราเมรัย (ละเว้นจากการดื่มของมึนเมา): พระสงฆ์มักสอนว่าข้อนี้สำคัญที่สุด เพราะเมื่อคนเราขาด \"สติ\" (mindfulness) จากความมึนเมา ก็มีโอกาสที่จะยับยั้งชั่งใจไม่ได้ และทำผิดศีลข้ออื่น ๆ ตามมาได้ง่ายขึ้น

ในวิถีชีวิตของคนไทย การ \"สมาทานศีล\" (formally undertaking the precepts) เป็นส่วนหนึ่งของเกือบทุกพิธีกรรมทางศาสนา แม้ว่าในชีวิตจริงการรักษาศีลให้บริสุทธิ์ครบทั้ง 5 ข้อตลอดเวลาอาจเป็นเรื่องท้าทาย แต่ชาวพุทธส่วนใหญ่ก็ยังใช้ศีล 5 เป็นเข็มทิศทางศีลธรรม เพื่อเตือนสติให้ดำเนินชีวิตด้วยความระมัดระวัง"""),
            ],
        ),
    ]
    generate_content_config = types.GenerateContentConfig(
        temperature=1,
        response_modalities=[
            "audio",
        ],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(
                    voice_name="Charon"
                )
            )
        ),
    )

    file_index = 0
    for chunk in client.models.generate_content_stream(
        model=model,
        contents=contents,
        config=generate_content_config,
    ):
        if (
            chunk.parts is None
        ):
            continue
        if chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
            file_name = f"ENTER_FILE_NAME_{file_index}"
            file_index += 1
            inline_data = chunk.parts[0].inline_data
            data_buffer = inline_data.data
            file_extension = mimetypes.guess_extension(inline_data.mime_type)
            if file_extension is None:
                file_extension = ".wav"
                data_buffer = convert_to_wav(inline_data.data, inline_data.mime_type)
            save_binary_file(f"{file_name}{file_extension}", data_buffer)
        else:
            if text := chunk.text:
                print(text)

def convert_to_wav(audio_data: bytes, mime_type: str) -> bytes:
    """Generates a WAV file header for the given audio data and parameters.

    Args:
        audio_data: The raw audio data as a bytes object.
        mime_type: Mime type of the audio data.

    Returns:
        A bytes object representing the WAV file header.
    """
    parameters = parse_audio_mime_type(mime_type)
    bits_per_sample = parameters["bits_per_sample"]
    sample_rate = parameters["rate"]
    num_channels = 1
    data_size = len(audio_data)
    bytes_per_sample = bits_per_sample // 8
    block_align = num_channels * bytes_per_sample
    byte_rate = sample_rate * block_align
    chunk_size = 36 + data_size  # 36 bytes for header fields before data chunk size

    # http://soundfile.sapp.org/doc/WaveFormat/

    header = struct.pack(
        "<4sI4s4sIHHIIHH4sI",
        b"RIFF",          # ChunkID
        chunk_size,       # ChunkSize (total file size - 8 bytes)
        b"WAVE",          # Format
        b"fmt ",          # Subchunk1ID
        16,               # Subchunk1Size (16 for PCM)
        1,                # AudioFormat (1 for PCM)
        num_channels,     # NumChannels
        sample_rate,      # SampleRate
        byte_rate,        # ByteRate
        block_align,      # BlockAlign
        bits_per_sample,  # BitsPerSample
        b"data",          # Subchunk2ID
        data_size         # Subchunk2Size (size of audio data)
    )
    return header + audio_data

def parse_audio_mime_type(mime_type: str) -> dict[str, int | None]:
    """Parses bits per sample and rate from an audio MIME type string.

    Assumes bits per sample is encoded like "L16" and rate as "rate=xxxxx".

    Args:
        mime_type: The audio MIME type string (e.g., "audio/L16;rate=24000").

    Returns:
        A dictionary with "bits_per_sample" and "rate" keys. Values will be
        integers if found, otherwise None.
    """
    bits_per_sample = 16
    rate = 24000

    # Extract rate from parameters
    parts = mime_type.split(";")
    for param in parts: # Skip the main type part
        param = param.strip()
        if param.lower().startswith("rate="):
            try:
                rate_str = param.split("=", 1)[1]
                rate = int(rate_str)
            except (ValueError, IndexError):
                # Handle cases like "rate=" with no value or non-integer value
                pass # Keep rate as default
        elif param.startswith("audio/L"):
            try:
                bits_per_sample = int(param.split("L", 1)[1])
            except (ValueError, IndexError):
                pass # Keep bits_per_sample as default if conversion fails

    return {"bits_per_sample": bits_per_sample, "rate": rate}


if __name__ == "__main__":
    generate()


