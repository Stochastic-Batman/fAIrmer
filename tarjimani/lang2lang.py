import re
import torch
from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, MarianTokenizer, MarianMTModel
from typing import Union


def create_models(lang_hotel: str = "ka", lang_guest: str = "en") -> Union[tuple[tuple[AutoTokenizer, AutoModelForSeq2SeqLM], tuple[AutoTokenizer, AutoModelForSeq2SeqLM]], str]:
    supported_language_pairs: list[tuple[str, str]] = [("en", "ka"), ("ka", "en"), ("en", "ru"), ("ru", "en")]
    if (lang_hotel, lang_guest) not in supported_language_pairs:
        return "<unsupported_language_pair>"

    # for translation to Georgian, only English to Georgian model exists and only that model name contains "synthetic": opus-mt-synthetic-en-ka
    model_name_h2g = f"Helsinki-NLP/opus-mt-{"synthetic-en" if lang_guest == "ka" else lang_hotel}-{lang_guest}"
    model_name_g2h = f"Helsinki-NLP/opus-mt-{"synthetic-en" if lang_hotel == "ka" else lang_guest}-{lang_hotel}"

    tokenizer_hotel = AutoTokenizer.from_pretrained(model_name_h2g)
    model_hotel = AutoModelForSeq2SeqLM.from_pretrained(model_name_h2g)

    tokenizer_guest = AutoTokenizer.from_pretrained(model_name_g2h)
    model_guest = AutoModelForSeq2SeqLM.from_pretrained(model_name_g2h)

    return (tokenizer_hotel, model_hotel), (tokenizer_guest, model_guest)


def _split_chunks(text: str, tokenizer, max_tokens: int = 450) -> list[str]:
    paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if p.strip()]
    chunks, current, current_len = [], [], 0

    for para in paragraphs:
        toks = len(tokenizer.encode(para))

        if current_len + toks > max_tokens and current:
            chunks.append('\n\n'.join(current))
            current, current_len = [para], toks
        else:
            current.append(para)
            current_len += toks
    if current:
        chunks.append('\n\n'.join(current))

    final = []
    for chunk in chunks:
        if len(tokenizer.encode(chunk)) <= max_tokens:
            final.append(chunk)
            continue
       
        sentences = re.split(r'(?<=[.!?])\s+', chunk)
        sub, sub_len = [], 0
        
        for sent in sentences:
            s_len = len(tokenizer.encode(sent))
            if sub_len + s_len > max_tokens and sub:
                final.append(' '.join(sub))
                sub, sub_len = [sent], s_len
            else:
                sub.append(sent)
                sub_len += s_len

        if sub:
            final.append(' '.join(sub))

    return final or [text]


def translate(msg: str, tokenizer: MarianTokenizer, model: MarianMTModel) -> str:
    parts = []

    for chunk in _split_chunks(msg, tokenizer):
        inputs = tokenizer(chunk, return_tensors="pt", truncation=True, max_length=512)    
        with torch.no_grad():
            outputs = model.generate(**inputs, num_beams=4, no_repeat_ngram_size=4, repetition_penalty=1.3, max_length=512)
        parts.append(tokenizer.decode(outputs[0], skip_special_tokens=True))
    
    return '\n\n'.join(parts)
