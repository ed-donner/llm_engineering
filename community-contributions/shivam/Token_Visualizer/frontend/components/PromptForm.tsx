'use client';

import { useState } from 'react';
import { Button } from './ui/button';
import { Label } from './ui/label';
import { Textarea } from './ui/textarea';
import { Slider } from './ui/slider';
import { Sparkles, Play } from 'lucide-react';

interface PromptFormProps {
  onSubmit: (prompt: string, maxTokens: number) => void;
  isLoading: boolean;
}

export function PromptForm({ onSubmit, isLoading }: PromptFormProps) {
  const [prompt, setPrompt] = useState('');
  const [maxTokens, setMaxTokens] = useState(50);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (prompt.trim()) {
      onSubmit(prompt, maxTokens);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 space-y-5">
      <div className="flex items-center gap-2 text-slate-800 font-semibold">
        <div className="w-8 h-8 bg-indigo-600 rounded-lg flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <span>Generate</span>
      </div>

      <div className="space-y-2">
        <Label htmlFor="prompt" className="text-sm font-medium text-slate-700">
          Prompt
        </Label>
        <Textarea
          id="prompt"
          placeholder="Enter your prompt..."
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          className="min-h-[80px] resize-none border-slate-200 focus:border-indigo-500 focus:ring-indigo-500 text-sm"
          required
        />
      </div>

      <div className="space-y-2">
        <Label className="text-sm font-medium text-slate-700">
          Max Tokens: <span className="text-indigo-600 font-bold">{maxTokens}</span>
        </Label>
        <Slider 
          value={maxTokens} 
          onValueChange={setMaxTokens} 
          min={10} 
          max={200} 
          step={10}
          className="mt-2"
        />
      </div>

      <Button 
        type="submit" 
        disabled={isLoading || !prompt.trim()}
        className="w-full h-10 text-sm font-medium bg-indigo-600 hover:bg-indigo-700 disabled:bg-slate-300 disabled:text-slate-500 rounded-lg transition-colors flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            Generating...
          </>
        ) : (
          <>
            <Play className="w-4 h-4" />
            Visualize Tokens
          </>
        )}
      </Button>
    </form>
  );
}