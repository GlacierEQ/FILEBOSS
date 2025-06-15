import json
from transformers import pipeline

class MultiAIChat:
    def __init__(self, models):
        self.models = models
        self.ai_pipelines = {model: pipeline("text-generation", model=model) for model in models}
        self.memory = {model: [] for model in models}  # Memory for each AI

    def send_prompt(self, prompt):
        responses = {}
        for model in self.models:
            response = self.ai_pipelines[model](prompt, max_length=50, do_sample=True)
            generated_text = response[0]['generated_text'].strip()
            responses[model] = generated_text
            self.memory[model].append({"prompt": prompt, "response": generated_text})  # Store in memory
        return responses

    def get_memory(self, model):
        return self.memory.get(model, [])

if __name__ == "__main__":
    models = ["gpt2", "distilgpt2"]  # Example models
    chat_system = MultiAIChat(models)
    prompt = "What is the future of AI?"
    responses = chat_system.send_prompt(prompt)
    print(json.dumps(responses, indent=2))
