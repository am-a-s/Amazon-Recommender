import torch
print("Torch Version:", torch.__version__)
print("CUDA Available:", torch.cuda.is_available())
print("CUDA Version:", torch.version.cuda)
print("Device Count:", torch.cuda.device_count())
print("Device Name:", torch.cuda.get_device_name(0) if torch.cuda.is_available() else "No GPU Found")

import requests
response = requests.get("http://127.0.0.1:8000/recommend?search_term=laptop")
print(response.status_code, response.text)
