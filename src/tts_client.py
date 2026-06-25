import os
from google import genai
from google.genai import types

class TTSClient:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        self.dev_mode = os.environ.get("DEV_MODE", "False").lower() == "true"
        
        if not self.dev_mode and not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        
        if not self.dev_mode:
            self.client = genai.Client(api_key=self.api_key)
        else:
            self.client = None
            
        self.model = "gemini-2.5-flash-preview-tts"

    def generate_audio_stream(self, text, voice="Charon", scene=None, audio_profile=None):
        """
        Generates audio using the Gemini TTS model.
        Yields (raw_audio_data, sample_rate) for each chunk.
        """
        if self.dev_mode:
            # Yield 2 seconds of silence (raw PCM 16-bit mono 24000Hz)
            # 24000 samples/sec * 2 bytes/sample * 2 sec = 96000 bytes
            yield b'\x00' * 96000, 24000
            return
        # Construct the prompt
        prompt_parts = [
            f"System Instruction: You must only use the {voice} preset. Do not alter the timbre, accent, or pitch across generations.\n\n",
            "Read the following transcript based on the audio profile.\n"
        ]
        
        if audio_profile:
            prompt_parts.append(f"\n# Audio Profile\n{audio_profile}\n")
        
        if scene:
            prompt_parts.append(f"\n## Scene:\n{scene}\n")
            
        prompt_parts.append(f"\n## Transcript:\n{text}")
        
        prompt_text = "".join(prompt_parts)

        contents = [
            types.Content(
                role="user",
                parts=[types.Part.from_text(text=prompt_text)],
            ),
        ]
        
        generate_content_config = types.GenerateContentConfig(
            temperature=1,
            response_modalities=["audio"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=voice
                    )
                )
            ),
        )

        for chunk in self.client.models.generate_content_stream(
            model=self.model,
            contents=contents,
            config=generate_content_config,
        ):
            if chunk.parts and chunk.parts[0].inline_data and chunk.parts[0].inline_data.data:
                inline_data = chunk.parts[0].inline_data
                sample_rate = self._parse_rate_from_mime(inline_data.mime_type)
                yield inline_data.data, sample_rate
            elif chunk.text:
                # Some chunks might contain text instead of audio data
                pass

    def _parse_rate_from_mime(self, mime_type: str) -> int:
        rate = 24000
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate = int(param.split("=", 1)[1])
                except (ValueError, IndexError):
                    pass
        return rate
