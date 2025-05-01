import torch
from transformers import MarianMTModel, MarianTokenizer
import whisper


def load_translation_model():
    model_name = "Helsinki-NLP/opus-mt-tc-big-en-ar"
    tokenizer = MarianTokenizer.from_pretrained(model_name)
    nmt_model = MarianMTModel.from_pretrained(model_name)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    nmt_model = nmt_model.to(device)
    return nmt_model, tokenizer


def load_whisper_model(model_name):
    if model_name in globals().get('model_cache', {}):
        return globals()['model_cache'][model_name]
    print(f"Loading Whisper model '{model_name}'...")
    model = whisper.load_model(model_name)
    if 'model_cache' not in globals():
        globals()['model_cache'] = {}
    globals()['model_cache'][model_name] = model
    return model
