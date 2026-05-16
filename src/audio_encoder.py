import lameenc

def encode_vbr_mp3(pcm_data: bytes, sample_rate: int, channels: int = 1, quality: int = 4) -> bytes:
    """
    Encodes raw 16-bit PCM data to VBR MP3.
    
    Args:
        pcm_data: Raw PCM 16-bit bytes.
        sample_rate: Sample rate in Hz.
        channels: Number of channels (default 1 for mono).
        quality: VBR quality (0-9, 0 is best). Default 4 (~165 kbps).
    """
    encoder = lameenc.Encoder()
    encoder.set_channels(channels)
    encoder.set_in_sample_rate(sample_rate)
    encoder.set_out_sample_rate(sample_rate)
    encoder.set_vbr(True)
    encoder.set_vbr_quality(quality)
    encoder.silence()
    
    mp3_data = encoder.encode(pcm_data)
    mp3_data += encoder.flush()
    return mp3_data
