import { Router, Request, Response } from 'express';
import { openaiService } from '../services/openai.js';

const router = Router();

router.post('/', async (req: Request, res: Response) => {
  const { prompt, maxTokens } = req.body;

  if (!prompt) {
    res.status(400).json({ error: 'Missing required field: prompt' });
    return;
  }

  res.setHeader('Content-Type', 'text/event-stream');
  res.setHeader('Cache-Control', 'no-cache');
  res.setHeader('Connection', 'keep-alive');
  res.setHeader('X-Accel-Buffering', 'no');

  try {
    for await (const prediction of openaiService.streamTokenPredictions(
      prompt,
      maxTokens || 50
    )) {
      res.write(`data: ${JSON.stringify({ type: 'token', data: prediction })}\n\n`);
    }

    res.write(`data: ${JSON.stringify({ type: 'done' })}\n\n`);
    res.end();
  } catch (error) {
    console.error('Error during prediction:', error);
    res.write(`data: ${JSON.stringify({ type: 'error', error: String(error) })}\n\n`);
    res.end();
  }
});

export default router;