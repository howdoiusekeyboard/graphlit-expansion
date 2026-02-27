'use client';

import { Maximize2, Minus, Plus } from 'lucide-react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Alert } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { useCommunityCitationNetwork } from '@/lib/hooks/useCommunities';
import { cn } from '@/lib/utils/cn';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

interface CommunityGraphProps {
  communityId: number;
  minYear?: number | null;
  className?: string;
}

interface GraphNode {
  id: string;
  title: string;
  year: number | null;
  citations: number;
  impactScore: number;
  val: number;
}

interface GraphLink {
  source: string;
  target: string;
}

/** Resolve a CSS custom property to a hex color (#rrggbb) safe for Canvas alpha appending. */
function resolveThemeHex(varName: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const raw = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  if (!raw) return fallback;

  // Normalize to a CSS color string the browser understands
  const cssColor =
    raw.startsWith('#') || raw.startsWith('rgb') || raw.startsWith('hsl') ? raw : `hsl(${raw})`;

  // Use a throwaway canvas to convert any CSS color → #rrggbb hex
  const ctx = document.createElement('canvas').getContext('2d');
  if (!ctx) return fallback;
  ctx.fillStyle = cssColor;
  return ctx.fillStyle; // always returns #rrggbb
}

export function CommunityGraph({ communityId, minYear, className }: CommunityGraphProps) {
  const router = useRouter();
  const { data, isLoading, error } = useCommunityCitationNetwork(communityId, minYear);

  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 800, height: 500 });

  const [primaryColor, setPrimaryColor] = useState('#e97316');
  const containerRef = useRef<HTMLDivElement>(null);
  // biome-ignore lint/suspicious/noExplicitAny: react-force-graph ref types are not exported
  const graph2DRef = useRef<any>(null);
  // biome-ignore lint/suspicious/noExplicitAny: react-force-graph ref types are not exported
  const graph3DRef = useRef<any>(null);

  // Resolve theme color on mount
  useEffect(() => {
    setPrimaryColor(resolveThemeHex('--primary', '#e97316'));
  }, []);

  // Track container dimensions via ResizeObserver (handles tab visibility)
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const observer = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const { width, height } = entry.contentRect;
      if (width > 0 && height > 0) {
        setDimensions({ width, height });
      }
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  // Transform API data → { nodes, links }
  const graphData = useMemo(() => {
    if (!data) return { nodes: [] as GraphNode[], links: [] as GraphLink[] };

    const nodes: GraphNode[] = data.papers.map((paper) => ({
      id: paper.paper_id,
      title: paper.title,
      year: paper.year,
      citations: paper.citations,
      impactScore: paper.impact_score ?? 0,
      val: 2 + (paper.impact_score ?? 0) / 10,
    }));

    const nodeIds = new Set(nodes.map((n) => n.id));
    const links: GraphLink[] = data.citations
      .filter((c) => nodeIds.has(c.source) && nodeIds.has(c.target))
      .map((c) => ({ source: c.source, target: c.target }));

    return { nodes, links };
  }, [data]);

  // Build adjacency map for hover highlighting
  const adjacencyMap = useMemo(() => {
    const map = new Map<string, Set<string>>();
    for (const link of graphData.links) {
      const src =
        typeof link.source === 'string' ? link.source : (link.source as { id: string }).id;
      const tgt =
        typeof link.target === 'string' ? link.target : (link.target as { id: string }).id;
      if (!map.has(src)) map.set(src, new Set());
      if (!map.has(tgt)) map.set(tgt, new Set());
      map.get(src)?.add(tgt);
      map.get(tgt)?.add(src);
    }
    return map;
  }, [graphData.links]);

  // Click → navigate to paper
  const handleNodeClick = useCallback(
    // biome-ignore lint/suspicious/noExplicitAny: node type from library
    (node: any) => {
      if (node?.id) router.push(`/paper/${node.id}`);
    },
    [router],
  );

  // Hover → track for highlighting
  // biome-ignore lint/suspicious/noExplicitAny: node type from library
  const handleNodeHover = useCallback((node: any) => {
    setHoveredNode(node?.id ?? null);
  }, []);

  // Configure force physics when ref is available or data changes
  // biome-ignore lint/correctness/useExhaustiveDependencies: graphData triggers force reconfiguration when new data arrives
  useEffect(() => {
    const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
    if (!ref.current) return;
    ref.current.d3Force?.('charge')?.strength?.(-300);
    ref.current.d3Force?.('link')?.distance?.(100);
    // Re-heat the simulation so new forces take effect, then fit
    ref.current.d3ReheatSimulation?.();
  }, [viewMode, graphData]);

  // Zoom to fit once the engine settles (called by onEngineStop)
  const handleEngineStop = useCallback(() => {
    const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
    ref.current?.zoomToFit?.(400, 40);
  }, [viewMode]);

  // Re-fit when container dimensions change (e.g., tab becomes visible)
  useEffect(() => {
    if (dimensions.width === 0 || dimensions.height === 0 || graphData.nodes.length === 0) return;
    const timer = setTimeout(() => {
      const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
      ref.current?.zoomToFit?.(400, 40);
    }, 300);
    return () => clearTimeout(timer);
  }, [dimensions.width, dimensions.height, viewMode, graphData.nodes.length]);

  // Custom 2D Canvas node painting — glow circles with labels
  const paintNode2D = useCallback(
    // biome-ignore lint/suspicious/noExplicitAny: node type from library
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const isHovered = hoveredNode === node.id;
      const isConnected = hoveredNode != null && adjacencyMap.get(hoveredNode)?.has(node.id);
      const isDimmed = hoveredNode != null && !isHovered && !isConnected;

      const radius = Math.sqrt(node.val || 1) * 4;
      const x = node.x ?? 0;
      const y = node.y ?? 0;

      // Glow
      if (!isDimmed) {
        const glowRadius = radius * (isHovered ? 3 : 2);
        const gradient = ctx.createRadialGradient(x, y, radius * 0.3, x, y, glowRadius);
        gradient.addColorStop(0, isHovered ? `${primaryColor}60` : `${primaryColor}25`);
        gradient.addColorStop(1, `${primaryColor}00`);
        ctx.beginPath();
        ctx.arc(x, y, glowRadius, 0, 2 * Math.PI);
        ctx.fillStyle = gradient;
        ctx.fill();
      }

      // Circle
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = isDimmed ? `${primaryColor}35` : primaryColor;
      ctx.fill();

      // Bright ring on hover
      if (isHovered) {
        ctx.strokeStyle = 'rgba(255,255,255,0.8)';
        ctx.lineWidth = 1.5 / globalScale;
        ctx.stroke();
      }

      // Label (only when zoomed in enough and not dimmed)
      if (globalScale > 0.7 && !isDimmed) {
        const label = node.title.length > 28 ? `${node.title.slice(0, 28)}...` : node.title;
        const fontSize = Math.max(11 / globalScale, 2.5);
        ctx.font = `600 ${fontSize}px "JetBrains Mono", monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = isHovered ? 'rgba(255,255,255,1)' : 'rgba(255,255,255,0.75)';
        ctx.fillText(label, x, y + radius + 3 / globalScale);
      }
    },
    [hoveredNode, adjacencyMap, primaryColor],
  );

  // Pointer hit area (slightly larger than visual node for easier clicking)
  const nodePointerArea = useCallback(
    // biome-ignore lint/suspicious/noExplicitAny: node type from library
    (node: any, color: string, ctx: CanvasRenderingContext2D) => {
      const radius = Math.sqrt(node.val || 1) * 4 + 6;
      ctx.beginPath();
      ctx.arc(node.x ?? 0, node.y ?? 0, radius, 0, 2 * Math.PI);
      ctx.fillStyle = color;
      ctx.fill();
    },
    [],
  );

  // Link color — highlight connected edges on hover
  const getLinkColor = useCallback(
    (link: Record<string, unknown>) => {
      if (!hoveredNode) return 'rgba(255, 255, 255, 0.1)';
      const src =
        typeof link.source === 'string' ? link.source : (link.source as { id: string })?.id;
      const tgt =
        typeof link.target === 'string' ? link.target : (link.target as { id: string })?.id;
      if (src === hoveredNode || tgt === hoveredNode) return `${primaryColor}bb`;
      return 'rgba(255, 255, 255, 0.04)';
    },
    [hoveredNode, primaryColor],
  );

  // Link width — thicken connected edges on hover
  const getLinkWidth = useCallback(
    (link: Record<string, unknown>) => {
      if (!hoveredNode) return 0.5;
      const src =
        typeof link.source === 'string' ? link.source : (link.source as { id: string })?.id;
      const tgt =
        typeof link.target === 'string' ? link.target : (link.target as { id: string })?.id;
      return src === hoveredNode || tgt === hoveredNode ? 2 : 0.2;
    },
    [hoveredNode],
  );

  // Zoom controls
  const handleZoomIn = () => {
    const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
    if (viewMode === '2d') {
      const z = ref.current?.zoom?.() ?? 1;
      ref.current?.zoom?.(z * 1.5, 300);
    } else {
      const pos = ref.current?.cameraPosition?.();
      if (pos) ref.current?.cameraPosition?.({ z: pos.z * 0.7 }, undefined, 300);
    }
  };

  const handleZoomOut = () => {
    const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
    if (viewMode === '2d') {
      const z = ref.current?.zoom?.() ?? 1;
      ref.current?.zoom?.(z / 1.5, 300);
    } else {
      const pos = ref.current?.cameraPosition?.();
      if (pos) ref.current?.cameraPosition?.({ z: pos.z * 1.4 }, undefined, 300);
    }
  };

  const handleFit = () => {
    const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
    ref.current?.zoomToFit?.(400, 60);
  };

  // Tooltip HTML (used by both 2D and 3D)
  // biome-ignore lint/suspicious/noExplicitAny: node type from library
  const getNodeTooltip = useCallback((node: any) => {
    return `<div style="background:rgba(10,10,18,0.95);border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:10px 14px;font-family:'JetBrains Mono',monospace;max-width:300px;backdrop-filter:blur(8px)">
			<div style="font-weight:900;font-size:12px;color:white;line-height:1.3">${node.title}</div>
			<div style="color:rgba(255,255,255,0.5);font-size:10px;margin-top:6px;font-weight:600;letter-spacing:0.05em;text-transform:uppercase">${node.year ?? 'N/A'} &middot; ${node.citations} citations &middot; Impact ${node.impactScore.toFixed(1)}</div>
		</div>`;
  }, []);

  // Loading state
  if (isLoading) {
    return (
      <div className="h-[400px] md:h-[500px] lg:h-[700px] flex items-center justify-center bg-secondary/20 rounded-2xl animate-pulse">
        <span className="text-muted-foreground font-bold uppercase text-xs tracking-widest">
          Mapping citation network...
        </span>
      </div>
    );
  }

  if (error) {
    return <Alert variant="destructive">Failed to load community graph</Alert>;
  }

  if (graphData.nodes.length === 0) {
    return (
      <div className="h-[400px] flex items-center justify-center bg-secondary/10 rounded-2xl border">
        <span className="text-muted-foreground font-bold uppercase text-xs tracking-widest">
          No network data available
        </span>
      </div>
    );
  }

  // Shared props between 2D and 3D
  const sharedProps = {
    graphData,
    width: dimensions.width,
    height: dimensions.height,
    nodeId: 'id' as const,
    nodeVal: 'val' as const,
    nodeLabel: getNodeTooltip,
    linkCurvature: 0.15,
    linkDirectionalParticles: 2,
    linkDirectionalParticleSpeed: 0.004,
    linkDirectionalParticleWidth: 1.5,
    linkDirectionalParticleColor: () => `${primaryColor}88`,
    onNodeClick: handleNodeClick,
    onNodeHover: handleNodeHover,
    onEngineStop: handleEngineStop,
    backgroundColor: 'rgba(0,0,0,0)',
    warmupTicks: 200,
    cooldownTime: 3000,
    d3VelocityDecay: 0.3,
  };

  return (
    <div
      ref={containerRef}
      className={cn(
        'relative h-[400px] md:h-[500px] lg:h-[700px] w-full border rounded-2xl bg-background/50 backdrop-blur-sm overflow-hidden',
        className,
      )}
    >
      {/* View Mode Toggle */}
      <div className="absolute top-4 right-4 z-10 flex gap-1.5">
        <Button
          variant={viewMode === '2d' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setViewMode('2d')}
          className="font-black text-[10px] uppercase tracking-widest h-7 px-3"
        >
          2D
        </Button>
        <Button
          variant={viewMode === '3d' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setViewMode('3d')}
          className="font-black text-[10px] uppercase tracking-widest h-7 px-3"
        >
          3D
        </Button>
      </div>

      {/* Zoom Controls — dark themed, high contrast */}
      <div className="absolute bottom-4 left-4 z-10 flex flex-col gap-1 p-1.5 rounded-xl bg-card/90 border border-border shadow-lg backdrop-blur-sm">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomIn}
          className="h-7 w-7 text-foreground hover:text-primary hover:bg-primary/10"
        >
          <Plus className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomOut}
          className="h-7 w-7 text-foreground hover:text-primary hover:bg-primary/10"
        >
          <Minus className="h-3.5 w-3.5" />
        </Button>
        <div className="h-px bg-border mx-1" />
        <Button
          variant="ghost"
          size="icon"
          onClick={handleFit}
          className="h-7 w-7 text-foreground hover:text-primary hover:bg-primary/10"
        >
          <Maximize2 className="h-3.5 w-3.5" />
        </Button>
      </div>

      {/* Stats Badge */}
      <div className="absolute top-4 left-4 z-10">
        <Badge
          variant="outline"
          className="bg-card/80 backdrop-blur-sm font-bold text-[10px] uppercase tracking-widest border-border"
        >
          {graphData.nodes.length} nodes · {graphData.links.length} edges
        </Badge>
      </div>

      {/* 2D Force Graph */}
      {viewMode === '2d' && dimensions.width > 0 && (
        <ForceGraph2D
          ref={graph2DRef}
          {...sharedProps}
          nodeCanvasObject={paintNode2D}
          nodeCanvasObjectMode={() => 'replace'}
          nodePointerAreaPaint={nodePointerArea}
          linkColor={getLinkColor}
          linkWidth={getLinkWidth}
          enableZoomInteraction
          enablePanInteraction
          enableNodeDrag
        />
      )}

      {/* 3D Force Graph */}
      {viewMode === '3d' && dimensions.width > 0 && (
        <ForceGraph3D
          ref={graph3DRef}
          {...sharedProps}
          nodeColor={(node: Record<string, unknown>) => {
            const nodeId = node.id as string;
            if (!hoveredNode) return primaryColor;
            if (nodeId === hoveredNode) return primaryColor;
            if (adjacencyMap.get(hoveredNode)?.has(nodeId)) return primaryColor;
            return `${primaryColor}50`;
          }}
          nodeOpacity={0.9}
          linkColor={getLinkColor}
          linkWidth={getLinkWidth}
          linkOpacity={0.3}
          showNavInfo={false}
          enableNavigationControls
        />
      )}
    </div>
  );
}
