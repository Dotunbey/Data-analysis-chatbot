from huggingface_hub import InferenceClient
import os

def load_mistral_pipeline():
    os.environ["HUGGINGFACEHUB_API_TOKEN"] = "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"

    client = InferenceClient(
        model="mistralai/Mistral-7B-Instruct-v0.3",
        token=os.environ["HUGGINGFACEHUB_API_TOKEN"]
    )

    return client
