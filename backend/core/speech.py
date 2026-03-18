"""
Azure Speech SDK wrappers for real-time STT and TTS for meetings.
Enhanced from ai-support-agent with continuous recognition support.
Requires AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.
"""
import os
import azure.cognitiveservices.speech as speechsdk
import tempfile
import io

KEY = os.getenv("AZURE_SPEECH_KEY")
REGION = os.getenv("AZURE_SPEECH_REGION")


def azure_stt_from_wav_bytes(wav_bytes: bytes, language: str = "en-US") -> str:
    \"\"\"
    Batch STT for WAV bytes (used for testing/file upload fallback).
    \"\"\"
    if not KEY or not REGION:
        raise RuntimeError("Azure Speech not configured. Set AZURE_SPEECH_KEY and AZURE_SPEECH_REGION.")
    
    speech_config = speechsdk.SpeechConfig(subscription=KEY, region=REGION)
    speech_config.speech_recognition_language = language
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
        f.write(wav_bytes)
        tmp = f.name
    
    audio_config = speechsdk.audio.AudioConfig(filename=tmp)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    result = recognizer.recognize_once()
    os.unlink(tmp)  # cleanup
    
    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return result.text
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return ""
    else:
        raise RuntimeError(f"STT failed: {result.reason} {result.text if result.text else ''}")


def azure_continuous_stt_start(language: str = "en-US"):
    \"\"\"
    Start continuous STT recognizer. Call .recognize() on chunks, .stop() to end.
    Returns recognizer object.
    \"\"\"
    if not KEY or not REGION:
        raise RuntimeError("Azure Speech not configured.")
    
    speech_config = speechsdk.SpeechConfig(subscription=KEY, region=REGION)
    speech_config.speech_recognition_language = language
    
    stream = speechsdk.audio.PushAudioInputStream()
    audio_config = speechsdk.audio.AudioConfig(stream=stream)
    
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_config)
    
    # Event handlers for real-time
    recognized = []
    
    def recognized_cb(evt):
        if evt.result.reason == speechsdk.ResultReason.RecognizedSpeech:
            recognized.append(evt.result.text)
    
    def canceled_cb(evt):
        print(f"Canceled: {evt.reason}")
    
    recognizer.recognized.connect(recognized_cb)
    recognizer.canceled.connect(canceled_cb)
    
    def get_transcript():
        return " ".join(recognized)
    
    def push_audio(wav_bytes):
        # Assumes 16kHz 16bit mono PCM WAV header stripped
        stream.write(wav_bytes)
    
    return recognizer, push_audio, get_transcript, stream


def azure_synthesize_to_wav_bytes(text: str, language: str = "en-US") -> bytes:
    \"\"\"
    TTS: Text to WAV bytes.
    \"\"\"
    if not KEY or not REGION:
        raise RuntimeError("Azure Speech not configured.")
    
    speech_config = speechsdk.SpeechConfig(subscription=KEY, region=REGION)
    # Meeting-friendly voice
    speech_config.speech_synthesis_voice_name = 'en-US-JennyNeural'
    
    audio_config = speechsdk.audio.AudioOutputConfig(use_default_speaker=False)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)
    
    result = synthesizer.speak_text_async(text).get()
    
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return result.audio_data
    else:
        raise RuntimeError(f"TTS failed: {result.reason}")

