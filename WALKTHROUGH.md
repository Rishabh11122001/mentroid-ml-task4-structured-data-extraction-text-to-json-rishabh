# How to explain this project

## One-minute explanation

This program converts a short biography into a JSON object with name, age and profession. An open-source instruction model performs the extraction locally. A separate validation layer checks that the response is real JSON with exactly the required keys and types. If validation fails, the model gets one retry. If that also fails, the program returns an error rather than pretending extraction succeeded.

I compare model outputs with manually labelled examples, and report formatting success separately from factual correctness. This matters because a valid JSON object can still contain a guessed age or incorrect profession.

## Follow the code in this order

1. `data/sample.txt`: the input biography.
2. `src/schema.py`: the output contract. `strict=True` prevents automatic conversion of a string age into an integer; `extra="forbid"` rejects extra fields.
3. `src/prompts.py`: instructions and two examples. The examples teach the desired output pattern; they do not train or update model weights.
4. `src/model.py`: loads the pretrained tokenizer and model, formats the prompt, and generates tokens on the CPU.
5. `src/extractor.py`: joins generation to validation and caps retries at one.
6. `extract.py`: reads input and writes validated output.
7. `evaluate.py`: compares predictions with expected values and records failures.

## Interview questions

**Did you train this model?**  
No. This is inference with pretrained instruction models. Few-shot prompting provides examples in the input; it is not fine-tuning.

**Why isn't `json.loads()` enough?**  
It checks JSON syntax but does not enforce our exact fields and types. Python's standard decoder also accepts duplicate keys and non-standard constants by default, so we explicitly reject those. Pydantic then enforces the schema.

**Why use `null`?**  
The paragraph may not state a field. A missing value is preferable to inventing an answer. The prompt asks for this policy; evaluation checks whether the model actually follows it.

**Why not calculate age from birth year?**  
Age depends on a reference date and potentially the birthday. This task is extraction, so the documented policy uses only an explicitly stated age.

**Does strict validation stop hallucinations?**  
No. An invented age of 65 has the right type and range. Schema validation cannot establish whether the biography supports it. This is why the results include exact-field and exact-record accuracy.

**Why one retry?**  
It gives the model validation feedback while bounding latency. It is not a guarantee of recovery. Both attempts are retained in the evaluation output.

**Why report baseline failures?**  
They explain model selection and expose limitations. A failed output is counted as incorrect, rather than removed from the denominator.

**Is the measured accuracy a general benchmark?**  
No. The examples are synthetic and small, and were used to compare models. A stronger assessment needs a separate, independently labelled test set.

## Before submitting

Run the commands yourself, read at least three failures in the saved predictions, and understand each function before discussing the project in an interview. Replace the email placeholder and inspect the public repository link before submitting the form.
