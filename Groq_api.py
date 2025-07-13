from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
from huggingface_hub import login

access_token = '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'
login(access_token)
model_name = 'microsoft/phi-2'

tokenizer = AutoTokenizer.from_pretrained(model_name, token=access_token)
model = AutoModelForCausalLM.from_pretrained(model_name, device_map='auto', torch_dtype=torch.float16, token=access_token)

user_input = 'i wanna an cheap, lightweight and strong for programming stuff.'

inputs = tokenizer.encode(user_input)

outputs = model.generate(**inputs, max_new_tokens=200)

response = tokenizer.decode(outputs[0], skip_special_tokens=True)
print(response)