from transformers import MarianMTModel, MarianTokenizer
import re
from PySide6.QtCore import QThread, Signal

class NmtModel(QThread):
    finished = Signal(str)
    progress = Signal(str)
    error = Signal(str)

    def __init__(self, transcription):
        super().__init__()
        self.transcription = transcription
        print(f"Initialized NMT Model with transcription length: {len(transcription)}")

    def run(self):
        try:
            # Load Arabic translation model
            model_name = 'Helsinki-NLP/opus-mt-tc-big-en-ar'
            model = MarianMTModel.from_pretrained(model_name)
            tokenizer = MarianTokenizer.from_pretrained(model_name)

            # Split transcription into manageable chunks
            # If you have timestamp format, modify this part accordingly
            # For now, we'll split by sentences
            sentences = re.split(r'(?<=[.!?])\s+', self.transcription)

            translated_sentences = []
            for sentence in sentences:
                if sentence.strip():  # Skip empty sentences
                    # Encode the sentence
                    inputs = tokenizer.encode(sentence, return_tensors='pt', max_length=512, truncation=True)
                    
                    # Generate translation
                    outputs = model.generate(inputs, max_length=512, num_beams=4, early_stopping=True)
                    
                    # Decode the translated text
                    translated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
                    translated_sentences.append(translated_text)

            # Join translated sentences
            translated_transcription = ' '.join(translated_sentences)

            # Emit the translated text
            self.finished.emit(translated_transcription)

            # Optional: Print progress
            self.progress.emit("Translation completed")

        except Exception as e:
            print(f"Translation error: {str(e)}")
            self.error.emit(str(e))