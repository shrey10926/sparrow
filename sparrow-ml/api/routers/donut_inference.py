import re
import time
import torch
from transformers import DonutProcessor, VisionEncoderDecoderModel
from config import settings
from huggingface_hub import login


login(settings.huggingface_key)

processor = DonutProcessor.from_pretrained(settings.processor)
model = VisionEncoderDecoderModel.from_pretrained(settings.model)

device = "cuda" if torch.cuda.is_available() else "cpu"
model.to(device)

def process_document_donut(image):
    start_time = time.time()

    # prepare encoder inputs
    pixel_values = processor(image, return_tensors="pt").pixel_values

    # prepare decoder inputs
    task_prompt = "<s_cord-v2>"
    decoder_input_ids = processor.tokenizer(task_prompt, add_special_tokens=False, return_tensors="pt").input_ids

    # generate answer
    outputs = model.generate(
        pixel_values.to(device),
        decoder_input_ids=decoder_input_ids.to(device),
        max_length=model.decoder.config.max_position_embeddings,
        early_stopping=True,
        pad_token_id=processor.tokenizer.pad_token_id,
        eos_token_id=processor.tokenizer.eos_token_id,
        use_cache=True,
        num_beams=1,
        bad_words_ids=[[processor.tokenizer.unk_token_id]],
        return_dict_in_generate=True,
    )

    # postprocess
    sequence = processor.batch_decode(outputs.sequences)[0]
    sequence = sequence.replace(processor.tokenizer.eos_token, "").replace(processor.tokenizer.pad_token, "")
    sequence = re.sub(r"<.*?>", "", sequence, count=1).strip()  # remove first task start token

    end_time = time.time()
    processing_time = end_time - start_time

    return processor.token2json(sequence), processing_time