import { ChatOpenAI } from '@langchain/openai';
import { initializeAgentExecutorWithOptions } from 'langchain/agents';
import { DynamicTool } from 'langchain/tools';
import fs from 'fs/promises';
import path from 'path';

async function getSystemPrompt() {
  const promptPath = path.join(process.cwd(), 'src', 'lib', 'ai', 'system_prompt.md');
  return fs.readFile(promptPath, 'utf-8');
}

async function loadTools() {
  const mcpConfigPath = path.join(process.cwd(), 'mcp_config.json');
  const mcpConfigData = await fs.readFile(mcpConfigPath, 'utf-8');
  const mcpConfig = JSON.parse(mcpConfigData);

  return mcpConfig.map((toolConfig: any) => {
    return new DynamicTool({
      name: toolConfig.name,
      description: toolConfig.description,
      func: async (input: string) => {
        try {
          const module = await import(toolConfig.package);
          const ToolClass = module.default; // Or the specific export
          const toolInstance = new ToolClass();
          // This assumes a standard 'run' method, which may need to be adapted
          return await toolInstance.run(input);
        } catch (error) {
          console.error(`Failed to execute tool ${toolConfig.name}:`, error);
          return `Error executing tool ${toolConfig.name}.`;
        }
      },
    });
  });
}

export async function runCognitiveTask(prompt: string) {
  const tools = await loadTools();
  const systemPrompt = await getSystemPrompt();
  const model = new ChatOpenAI({ temperature: 0.7, modelName: 'gpt-4o' });

  const executor = await initializeAgentExecutorWithOptions(tools, model, {
    agentType: 'openai-functions',
    verbose: true,
    agentArgs: {
      prefix: systemPrompt,
    },
  });

  console.log(`Running Omni-Cognitive task: ${prompt}`);
  const result = await executor.run(prompt);
  console.log(`Omni-Cognitive task result: ${result}`);
  return result;
}
