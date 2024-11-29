import re
from transformers import MarianMTModel, MarianTokenizer

# Extract the sentences from the input text
input_text = """
[0.00 - 10.52]  Hello and welcome to the Los Poyers of the Manus Family.
[10.52 - 13.28]  My name is Gustavo, but you can call me Gus.
[13.28 - 16.52]  I am thrilled that you will be joining our team.
[16.52 - 22.24]  Each and every day we serve our customers exceptional food with impeccable service.
[22.24 - 24.92]  We take pride in everything that we do.
[24.92 - 31.24]  And after this 10 week online seminar, I am confident that you fit right in.
[31.24 - 34.72]  I like to think I see things in people.
[34.72 - 39.68]  To begin, I'd like to talk about the cornerstone of the Los Poyers of Manus brand,
[39.68 - 40.68]  communication.
"""

sentences = re.findall(r'\[(.*?)\]\s+(.*)', input_text)

# Load the pre-trained model and tokenizer
model_name = 'Helsinki-NLP/opus-mt-tc-big-en-ar'
model = MarianMTModel.from_pretrained(model_name)
tokenizer = MarianTokenizer.from_pretrained(model_name)

# Translate the sentences
translated_sentences = []
for _, sentence in sentences:
    encoded_text = tokenizer.encode(sentence, return_tensors='pt')
    output_ids = model.generate(encoded_text, max_length=100, num_beams=4, early_stopping=True)
    translated_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    translated_sentences.append(translated_text)

# Combine the timestamps and translated sentences
output_text = '\n'.join([f'[{timestamp}] {translated}' for timestamp, translated in zip([timestamp for timestamp, _ in sentences], translated_sentences)])

print(output_text)
with open("transcription.txt", "w", encoding="utf-8") as file:
            file.write(output_text)
            print("Transcription saved to file") 