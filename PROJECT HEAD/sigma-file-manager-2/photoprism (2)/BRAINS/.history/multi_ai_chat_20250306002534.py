import json
from transformers import pipeline

class MultiAIChat:
    def __init__(self, models):
        self.models = models
        self.ai_pipelines = {model: pipeline("text-generation", model=model) for model in models}
        self.memory = {model: [] for model in models}  # Memory for each AI
        self.memory_limit = 5  # Limit the number of stored interactions per model

    def send_prompt(self, user_prompt):
        model_responses = {}
        for model in self.models:
            context = self.memory[model][-self.memory_limit:]  # Get recent interactions for context
            if context:
                user_prompt = f"{' '.join([entry['prompt'] for entry in context])} {user_prompt}"  # Include context in the prompt

            response = self.ai_pipelines[model](user_prompt, max_length=50, do_sample=True)
            if len(self.memory[model]) >= self.memory_limit:
                self.memory[model].pop(0)  # Remove the oldest interaction if limit is reached

            generated_text = response[0]['generated_text'].strip()
            model_responses[model] = generated_text
            self.memory[model].append({"prompt": user_prompt, "response": generated_text})  # Store in memory
        return model_responses

    def get_memory(self, model):
        return self.memory.get(model, [])

if __name__ == "__main__":
    models = ["gpt2", "distilgpt2"]  # Example models
    chat_system = MultiAIChat(models)
    user_prompt = "What is the future of AI?"
    responses = chat_system.send_prompt(user_prompt)
    print(json.dumps(responses, indent=2))
