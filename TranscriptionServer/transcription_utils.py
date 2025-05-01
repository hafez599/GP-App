import itertools
import os


def transcribe_segment(model, audio_path, start_time, end_time):
    segment_transcription = model.transcribe(audio_path)
    adjusted_segments = []
    for idx, segment in enumerate(segment_transcription["segments"], start=1):
        adj_segment = segment.copy()
        adj_segment['start'] = max(
            start_time, adj_segment['start'] + start_time)
        adj_segment['end'] = min(end_time, adj_segment['end'] + start_time)
        if adj_segment['end'] <= adj_segment['start']:
            continue
        adjusted_segments.append(adj_segment)
    return adjusted_segments


def write_srt_segment(segment, srt_path, index):
    with open(srt_path, "a", encoding="utf-8") as f:
        start = format_timestamp(segment['start'])
        end = format_timestamp(segment['end'])
        f.write(f"{index}\n")
        f.write(f"{start} --> {end}\n")
        f.write(f"{segment['text'].strip()}\n\n")


def format_timestamp(seconds):
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    seconds = seconds % 60
    milliseconds = int((seconds - int(seconds)) * 1000)
    return f"{hours:02d}:{minutes:02d}:{int(seconds):02d},{milliseconds:03d}"
