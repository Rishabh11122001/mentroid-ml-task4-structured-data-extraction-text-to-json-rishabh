from .prompts import make_prompt
from .schema import validate_output

class ExtractionError(ValueError):
    def __init__(self, attempts):
        self.attempts = attempts
        super().__init__("Model failed strict JSON validation after all attempts")

def extract(text, model, retries=1):
    if not text.strip():
        raise ValueError("Biography must not be empty")
    if len(text) > 6000:
        raise ValueError("Biography must be a short paragraph (maximum 6000 characters)")
    if retries not in (0, 1):
        raise ValueError("retries must be 0 or 1")
    attempts, feedback = [], None
    for _ in range(retries + 1):
        raw = model.generate(make_prompt(text, feedback))
        try:
            person = validate_output(raw)
        except ValueError as error:
            feedback = str(error)[:1200]
            attempts.append({"raw": raw, "valid": False, "error": feedback})
        else:
            attempts.append({"raw": raw, "valid": True, "error": None})
            return person, attempts
    raise ExtractionError(attempts)
