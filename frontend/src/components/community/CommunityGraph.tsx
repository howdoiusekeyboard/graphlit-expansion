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
import { useCallback, useEffect } from 'react';
import '@xyflow/react/dist/style.css';
import { Alert } from '@/components/ui/alert';
import { useCommunityCitationNetwork } from '@/lib/hooks/useCommunities';
import { cn } from '@/lib/utils/cn';

interface CommunityGraphProps {
  communityId: number;
  className?: string;
}

export function CommunityGraph({ communityId, className }: CommunityGraphProps) {
  const { data, isLoading, error } = useCommunityCitationNetwork(communityId);

  const [nodes, setNodes, onNodesChange] = useNodesState<Node>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<Edge>([]);

  const transformData = useCallback(() => {
    if (!data) return;

    const newNodes: Node[] = data.papers.map((paper: any) => ({
      id: paper.paper_id,
      type: 'default',
      data: {
        label: `${paper.title.slice(0, 30)}...`,
        impact: paper.impact_score,
      },
      position: { x: paper.x || Math.random() * 500, y: paper.y || Math.random() * 500 },
      style: {
        background: 'hsl(var(--primary))',
        color: 'white',
        borderRadius: '50%',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        fontSize: '10px',
        width: Math.max(60, paper.impact_score * 1.5),
        height: Math.max(60, paper.impact_score * 1.5),
        border: 'none',
      },
    }));

    const newEdges: Edge[] = data.citations.map((citation: any, idx: number) => ({
      id: `e-${idx}`,
      source: citation.source,
      target: citation.target,
      type: 'smoothstep',
      style: { stroke: '#cbd5e1', strokeWidth: 1 },
    }));

    setNodes(newNodes);
    setEdges(newEdges);
  }, [data, setNodes, setEdges]);

  useEffect(() => {
    transformData();
  }, [transformData]);

  if (isLoading) {
    return (
      <div className="h-[500px] flex items-center justify-center bg-secondary/20 rounded-lg animate-pulse">
        <span className="text-muted-foreground">Mapping community citation network...</span>
      </div>
    );
  }

  if (error) {
    return <Alert variant="destructive">Failed to load community graph</Alert>;
  }

  return (
    <div
      className={cn(
        'h-[500px] w-full border rounded-lg bg-background/50 backdrop-blur-sm',
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
      >
        <Background gap={20} color="#f1f5f9" />
        <Controls />
        <MiniMap nodeColor="hsl(var(--primary))" maskColor="rgba(0, 0, 0, 0.1)" />
      </ReactFlow>
    </div>
  );
}
