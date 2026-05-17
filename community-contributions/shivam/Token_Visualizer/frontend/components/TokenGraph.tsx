'use client';

import { useCallback, useEffect } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  Node,
  Edge,
  MarkerType,
} from '@xyflow/react';
import '@xyflow/react/dist/style.css';
import { TokenNode } from './TokenNode';
import { TokenPrediction } from '@/lib/api';
import { GitBranch, Loader2 } from 'lucide-react';

const nodeTypes = {
  token: TokenNode,
};

interface TokenGraphProps {
  predictions: TokenPrediction[];
  isStreaming: boolean;
}

function GraphContent({ predictions, isStreaming }: TokenGraphProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);
  const { fitView } = useReactFlow();

  const buildGraph = useCallback(() => {
    const newNodes: Node[] = [];
    const newEdges: Edge[] = [];

    const centerX = 400;
    let currentY = 40;

    newNodes.push({
      id: 'start',
      type: 'token',
      position: { x: centerX, y: currentY },
      data: { token: '', probability: 1, isStart: true },
    });

    currentY += 100;

    predictions.forEach((pred, index) => {
      const nodeId = `token-${index}`;
      
      newNodes.push({
        id: nodeId,
        type: 'token',
        position: { x: centerX, y: currentY },
        data: {
          token: pred.token,
          probability: pred.probability,
          alternatives: pred.alternatives,
        },
      });

      newEdges.push({
        id: `edge-${index}`,
        source: index === 0 ? 'start' : `token-${index - 1}`,
        target: nodeId,
        type: 'smoothstep',
        style: { stroke: '#6366f1', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
      });

      if (pred.alternatives && pred.alternatives.length > 0) {
        pred.alternatives.forEach((alt, altIndex) => {
          const altNodeId = `alt-${index}-${altIndex}`;
          const xOffset = altIndex === 0 ? -220 : 220;

          newNodes.push({
            id: altNodeId,
            type: 'token',
            position: { x: centerX + xOffset, y: currentY + 8 },
            data: {
              token: alt.token,
              probability: alt.prob,
              alternatives: [],
            },
          });

          newEdges.push({
            id: `edge-alt-${index}-${altIndex}`,
            source: index === 0 ? 'start' : `token-${index - 1}`,
            target: altNodeId,
            type: 'smoothstep',
            style: { stroke: '#cbd5e1', strokeWidth: 1.5, strokeDasharray: '5,3' },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#cbd5e1' },
          });
        });
      }

      currentY += 120;
    });

    if (predictions.length > 0) {
      newNodes.push({
        id: 'end',
        type: 'token',
        position: { x: centerX, y: currentY + 20 },
        data: { token: '', probability: 1, isEnd: true },
      });

      newEdges.push({
        id: `edge-end`,
        source: `token-${predictions.length - 1}`,
        target: 'end',
        type: 'smoothstep',
        style: { stroke: '#6366f1', strokeWidth: 2 },
        markerEnd: { type: MarkerType.ArrowClosed, color: '#6366f1' },
      });
    }

    setNodes(newNodes);
    setEdges(newEdges);

    setTimeout(() => {
      fitView({ 
        padding: 0.25, 
        duration: 500,
        minZoom: 0.3
      });
    }, 100);

  }, [predictions, setNodes, setEdges, fitView]);

  useEffect(() => {
    if (predictions.length > 0) {
      buildGraph();
    }
  }, [predictions, buildGraph]);

  if (predictions.length === 0 && !isStreaming) {
    return (
      <div className="flex flex-col items-center justify-center h-[400px] text-slate-400">
        <GitBranch className="w-12 h-12 mb-3 opacity-50" />
        <p className="text-sm">No visualization yet</p>
      </div>
    );
  }

  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      onEdgesChange={onEdgesChange}
      nodeTypes={nodeTypes}
      fitView
      fitViewOptions={{ padding: 0.25, minZoom: 0.3 }}
      minZoom={0.2}
      maxZoom={2}
      defaultViewport={{ x: 0, y: 0, zoom: 0.8 }}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#e2e8f0" gap={16} size={1} />
      <Controls 
        className="!bg-white !border-slate-200 !rounded-lg !shadow-sm"
        showZoom={true}
        showFitView={true}
        showInteractive={false}
      />
    </ReactFlow>
  );
}

export function TokenGraph({ predictions, isStreaming }: TokenGraphProps) {
  return (
    <div className="h-[500px] relative">
      {isStreaming && (
        <div className="absolute top-3 left-3 z-10 flex items-center gap-2 px-3 py-1.5 bg-amber-50 border border-amber-200 rounded-full text-xs text-amber-700">
          <Loader2 className="w-3 h-3 animate-spin" />
          <span className="font-medium">Streaming...</span>
        </div>
      )}
      <ReactFlowProvider>
        <GraphContent predictions={predictions} isStreaming={isStreaming} />
      </ReactFlowProvider>
    </div>
  );
}