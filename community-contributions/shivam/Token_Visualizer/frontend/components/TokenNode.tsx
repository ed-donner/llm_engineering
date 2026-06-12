'use client';

import { Handle, Position, NodeProps } from '@xyflow/react';

interface TokenNodeData {
  token: string;
  probability: number;
  alternatives?: { token: string; prob: number }[];
  isStart?: boolean;
  isEnd?: boolean;
}

type TokenNodeProps = NodeProps & { data: TokenNodeData };

export function TokenNode(props: TokenNodeProps) {
  const { data: nodeData } = props;

  if (nodeData.isStart) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white font-semibold rounded-full shadow-md text-xs">
        <div className="w-2 h-2 bg-white/40 rounded-full animate-pulse" />
        START
      </div>
    );
  }

  if (nodeData.isEnd) {
    return (
      <div className="flex items-center gap-2 px-4 py-2 bg-rose-500 text-white font-semibold rounded-full shadow-md text-xs">
        END
        <div className="w-2 h-2 bg-white/40 rounded-full" />
      </div>
    );
  }

  const probPercent = nodeData.probability * 100;
  const probColor = probPercent >= 70 ? 'bg-emerald-500' : probPercent >= 50 ? 'bg-amber-500' : 'bg-rose-500';
  const probTextColor = probPercent >= 70 ? 'text-emerald-600' : probPercent >= 50 ? 'text-amber-600' : 'text-rose-600';

  return (
    <div className="min-w-[140px]">
      <Handle 
        type="target" 
        position={Position.Top} 
        className="!w-2.5 !h-2.5 !bg-slate-400 !border-2 !border-white !-top-1.5" 
      />
      
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div className="px-3 py-2 bg-slate-50 border-b border-slate-100">
          <span className="text-[10px] font-medium text-slate-400 uppercase tracking-wider">
            Selected
          </span>
        </div>
        
        <div className="p-3 space-y-2">
          <div className="text-sm font-mono font-bold text-slate-800 whitespace-pre-wrap leading-tight">
            {nodeData.token}
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-500">Confidence</span>
              <span className={`font-semibold ${probTextColor}`}>{probPercent.toFixed(0)}%</span>
            </div>
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full ${probColor} transition-all duration-300 rounded-full`}
                style={{ width: `${probPercent}%` }}
              />
            </div>
          </div>

          {nodeData.alternatives && nodeData.alternatives.length > 0 && (
            <div className="pt-2 border-t border-slate-100">
              <div className="text-[10px] font-medium text-slate-400 mb-1.5">
                Other options
              </div>
              <div className="space-y-1">
                {nodeData.alternatives.map((alt, i) => (
                  <div key={i} className="flex items-center justify-between text-xs bg-slate-50 rounded px-2 py-1">
                    <span className="font-mono text-slate-600">{alt.token}</span>
                    <span className="text-slate-400 font-medium">{(alt.prob * 100).toFixed(0)}%</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
      
      <Handle 
        type="source" 
        position={Position.Bottom} 
        className="!w-2.5 !h-2.5 !bg-slate-400 !border-2 !border-white !-bottom-1.5" 
      />
    </div>
  );
}