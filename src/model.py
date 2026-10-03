"""Local inference. Downloads public weights on first use, with no hosted inference API."""
import torch
from transformers import AutoConfig, AutoTokenizer, AutoModelForSeq2SeqLM, AutoModelForCausalLM

class LocalModel:
    def __init__(self, model_id="Qwen/Qwen2.5-0.5B-Instruct", revision="main", threads=4):
        if threads < 1:
            raise ValueError("threads must be positive")
        torch.set_num_threads(threads)
        self.model_id = model_id
        self.tokenizer = AutoTokenizer.from_pretrained(model_id, revision=revision)
        config = AutoConfig.from_pretrained(model_id, revision=revision)
        self.is_encoder_decoder = config.is_encoder_decoder
        cls = AutoModelForSeq2SeqLM if self.is_encoder_decoder else AutoModelForCausalLM
        self.model = cls.from_pretrained(model_id, revision=revision, dtype=torch.float32)
        self.model.eval()
        self.revision = getattr(self.model.config, "_commit_hash", None) or revision

    def generate(self, prompt):
        if not self.is_encoder_decoder:
            prompt = self.tokenizer.apply_chat_template(
                [{"role": "user", "content": prompt}], tokenize=False, add_generation_prompt=True
            )
        inputs = self.tokenizer(prompt, return_tensors="pt", add_special_tokens=self.is_encoder_decoder)
        limit = 512 if self.is_encoder_decoder else 2048
        if inputs.input_ids.shape[1] > limit:
            raise ValueError(f"Prompt exceeds {limit} input tokens; shorten the biography")
        with torch.inference_mode():
            output = self.model.generate(
                **inputs, max_new_tokens=128, do_sample=False,
                pad_token_id=self.tokenizer.pad_token_id if self.tokenizer.pad_token_id is not None else self.tokenizer.eos_token_id,
            )
        ids = output[0] if self.is_encoder_decoder else output[0, inputs.input_ids.shape[1]:]
        return self.tokenizer.decode(ids, skip_special_tokens=True).strip()
