import type { NextApiRequest, NextApiResponse } from 'next';
import { runCognitiveTask } from '../../lib/ai/agent';

export default async function handler(
  req: NextApiRequest,
  res: NextApiResponse
) {
  if (req.method === 'POST') {
    const { prompt } = req.body;
    const result = await runCognitiveTask(prompt);
    res.status(200).json({ result });
  } else {
    res.status(200).json({ status: 'All systems nominal. Cognitive Core is online.' });
  }
}
