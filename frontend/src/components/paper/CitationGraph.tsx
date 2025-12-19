'use client';

import {
  Background,
  ConnectionMode,
  Controls,
  type Edge,
  MiniMap,
  type Node,
  ReactFlow,
  useEdgesState,
  useNodesState,
} from '@xyflow/react';
import { useEffect } from 'react';
import '@xyflow/react/dist/style.css';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { usePaperCitationNetwork } from '@/lib/hooks/usePapers';
import { cn } from '@/lib/utils/cn';
import { truncate } from '@/lib/utils/formatters';

interface CitationGraphProps {
  paperId: string;
  className?: string;
}

export function CitationGraph({ paperId, className }: CitationGraphProps) {
  const { data, isLoading, error } = usePaperCitationNetwork(paperId);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  // Transform API data to React Flow nodes/edges
  useEffect(() => {
    if (!data) return;

    const newNodes: Node[] = data.papers.map((paper) => ({
      id: paper.paper_id,
      type: 'default',
      data: {
        label: truncate(paper.title, 30),
      },
      position: {
        x: paper.x ?? Math.random() * 800,
        y: paper.y ?? Math.random() * 600,
      },
      style: {
        background: getCommunityColor(paper.community ?? 0),
        color: '#fff',
        borderRadius: '12px',
        padding: '10px',
        fontSize: '10px',
        fontWeight: 'bold' as const,
        width: Math.max(120, (paper.impact_score ?? 50) * 1.5),
        height: 50,
        border: paper.paper_id === paperId ? '3px solid #f97316' : 'none',
        boxShadow: paper.paper_id === paperId ? '0 0 20px rgba(249, 115, 22, 0.4)' : 'none',
      },
    }));

    const newEdges: Edge[] = data.citations.map((citation, idx) => ({
      id: `e-${idx}`,
      source: citation.source,
      target: citation.target,
      type: 'smoothstep',
      animated: citation.source === paperId || citation.target === paperId,
      style: { stroke: '#475569', strokeWidth: 1.5 },
    }));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [data, paperId, setNodes, setEdges]);

  if (isLoading) {
    return (
      <div
        className={cn(
          'h-[500px] w-full border rounded-3xl bg-muted/20 flex flex-col items-center justify-center space-y-4',
          className,
        )}
      >
        <Skeleton className="h-12 w-12 rounded-full" />
        <p className="text-sm font-bold text-muted-foreground">Mapping Citation Network...</p>
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="rounded-3xl">
        <AlertDescription>Failed to load citation graph for this paper.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div
      className={cn(
        'h-[500px] w-full border rounded-3xl overflow-hidden bg-card/50 backdrop-blur-sm',
        className,
      )}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        connectionMode={ConnectionMode.Loose}
        fitView
        minZoom={0.2}
        maxZoom={1.5}
      >
        <Background color="#334155" gap={20} />
        <Controls className="fill-foreground" />
        <MiniMap
          nodeColor={(node) => node.style?.background as string}
          maskColor="rgba(0, 0, 0, 0.1)"
          className="bg-card border rounded-lg"
        />
      </ReactFlow>
    </div>
  );
}

function getCommunityColor(communityId: number): string {
  const colors = [
    '#3b82f6',
    '#ef4444',
    '#10b981',
    '#f59e0b',
    '#8b5cf6',
    '#ec4899',
    '#14b8a6',
    '#f97316',
    '#6366f1',
    '#84cc16',
  ];
  return colors[communityId % colors.length] || '#3b82f6';
}
