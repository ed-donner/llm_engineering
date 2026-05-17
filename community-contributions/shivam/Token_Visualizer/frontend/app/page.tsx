'use client';

import { useState, useCallback } from 'react';
import { PromptForm } from '@/components/PromptForm';
import { TokenGraph } from '@/components/TokenGraph';
import { TokenPrediction, streamTokenPredictions } from '@/lib/api';
import { Brain, GitBranch, List, Loader2, Zap } from 'lucide-react';

type ViewTab = 'graph' | 'table';

export default function Home() {
  const [predictions, setPredictions] = useState<TokenPrediction[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [activeTab, setActiveTab] = useState<ViewTab>('graph');
  const [graphKey, setGraphKey] = useState(0);

  const handleSubmit = useCallback(
    async (prompt: string, maxTokens: number) => {
      setPredictions([]);
      setIsLoading(true);
      setIsStreaming(true);
      setActiveTab('graph');

      try {
        const generator = streamTokenPredictions(prompt, maxTokens);

        for await (const prediction of generator) {
          setPredictions((prev) => [...prev, prediction]);
        }

        setGraphKey(k => k + 1);
      } catch (error) {
        console.error('Error:', error);
        alert(`Error: ${error instanceof Error ? error.message : 'Unknown error'}`);
      } finally {
        setIsLoading(false);
        setIsStreaming(false);
      }
    },
    []
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        <header className="text-center">
          <div className="inline-flex items-center gap-3 mb-4">
            <div className="w-12 h-12 bg-indigo-600 rounded-xl flex items-center justify-center shadow-md">
              <Brain className="w-6 h-6 text-white" />
            </div>
            <h1 className="text-2xl font-bold text-slate-900 tracking-tight">
              Token Visualizer
            </h1>
          </div>
          <p className="text-slate-500 text-sm max-w-lg mx-auto">
            Visualize how AI models predict tokens by showing the highest probability selection from all alternatives
          </p>
        </header>

        <div className="max-w-2xl mx-auto">
          <PromptForm onSubmit={handleSubmit} isLoading={isLoading} />
        </div>

        {predictions.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 overflow-hidden">
            <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200 bg-slate-50/50">
              <div className="flex items-center gap-1">
                <button
                  onClick={() => setActiveTab('graph')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === 'graph'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <GitBranch className="w-4 h-4" />
                  Graph
                </button>
                <button
                  onClick={() => setActiveTab('table')}
                  className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    activeTab === 'table'
                      ? 'bg-indigo-600 text-white shadow-sm'
                      : 'text-slate-600 hover:bg-slate-100'
                  }`}
                >
                  <List className="w-4 h-4" />
                  Table
                </button>
              </div>
              
              <div className="flex items-center gap-3">
                {isStreaming && (
                  <span className="flex items-center gap-2 text-xs text-amber-600 bg-amber-50 px-2 py-1 rounded-full">
                    <Loader2 className="w-3 h-3 animate-spin" />
                    Streaming
                  </span>
                )}
                <span className="text-xs text-slate-400 font-medium">
                  {predictions.length} tokens
                </span>
              </div>
            </div>

            <div className="relative">
              {activeTab === 'graph' ? (
                <TokenGraph 
                  key={graphKey} 
                  predictions={predictions} 
                  isStreaming={isStreaming} 
                />
              ) : (
                <div className="max-h-[500px] overflow-auto">
                  <table className="w-full text-sm">
                    <thead className="bg-slate-50 sticky top-0 z-10">
                      <tr className="border-b border-slate-200">
                        <th className="text-left px-4 py-3 font-semibold text-slate-600 text-xs uppercase tracking-wide">#</th>
                        <th className="text-left px-4 py-3 font-semibold text-slate-600 text-xs uppercase tracking-wide">Token</th>
                        <th className="text-right px-4 py-3 font-semibold text-slate-600 text-xs uppercase tracking-wide">Probability</th>
                        <th className="text-right px-4 py-3 font-semibold text-slate-600 text-xs uppercase tracking-wide">Alternatives</th>
                      </tr>
                    </thead>
                    <tbody>
                      {predictions.map((pred, i) => (
                        <tr key={i} className="border-b border-slate-100 hover:bg-slate-50/50">
                          <td className="px-4 py-3 text-slate-400 font-mono text-xs">{i + 1}</td>
                          <td className="px-4 py-3">
                            <span className="font-mono font-semibold text-slate-800 bg-slate-100 px-2 py-1 rounded">
                              {pred.token}
                            </span>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center justify-end gap-3">
                              <div className="w-20 h-1.5 bg-slate-100 rounded-full overflow-hidden">
                                <div 
                                  className="h-full bg-indigo-600 rounded-full"
                                  style={{ width: `${pred.probability * 100}%` }}
                                />
                              </div>
                              <span className="font-semibold text-slate-700 text-xs w-12 text-right">
                                {(pred.probability * 100).toFixed(1)}%
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex flex-wrap justify-end gap-1">
                              {pred.alternatives.length > 0 ? (
                                pred.alternatives.map((a, j) => (
                                  <span key={j} className="inline-flex items-center gap-1 bg-slate-50 border border-slate-200 px-2 py-0.5 rounded text-xs">
                                    <span className="font-mono text-slate-600">{a.token}</span>
                                    <span className="text-slate-400">{(a.prob * 100).toFixed(0)}%</span>
                                  </span>
                                ))
                              ) : (
                                <span className="text-slate-300">—</span>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}

        {predictions.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center py-16 text-center">
            <div className="w-20 h-20 bg-slate-100 rounded-2xl flex items-center justify-center mb-4">
              <Zap className="w-10 h-10 text-slate-300" />
            </div>
            <p className="text-slate-500 font-medium">
              Enter a prompt and click <span className="text-indigo-600">Visualize Tokens</span> to start
            </p>
          </div>
        )}
      </div>
    </div>
  );
}