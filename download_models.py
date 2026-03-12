import os  # used to check environment variables
from transformers import AutoModelForCausalLM, AutoTokenizer  # used to download the models

# run this script once at home while you have internet
# it downloads both models into a local cache on your machine
# after this you will not need internet to run either app

# make sure TRANSFORMERS_OFFLINE is not set when running this script
# otherwise it will refuse to download anything
if os.environ.get("TRANSFORMERS_OFFLINE") == "1":
    print("error: TRANSFORMERS_OFFLINE is set to 1, unset it before running this script")
    exit()

print("downloading smollm2 135m (about 270mb)...")
AutoTokenizer.from_pretrained("HuggingFaceTB/SmolLM2-135M-Instruct")  # downloads and caches the tokenizer
AutoModelForCausalLM.from_pretrained("HuggingFaceTB/SmolLM2-135M-Instruct")  # downloads and caches the model weights
print("smollm2 135m done\n")

print("downloading tinyllama 1.1b (about 2.2gb, this will take a while)...")
AutoTokenizer.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")  # downloads and caches the tokenizer
AutoModelForCausalLM.from_pretrained("TinyLlama/TinyLlama-1.1B-Chat-v1.0")  # downloads and caches the model weights
print("tinyllama 1.1b done\n")

print("both models are now saved locally and will work offline")
print("you can now run app_smollm.py and app_tinyllama.py without internet")