'use client';

import { Maximize2, Minus, Plus } from 'lucide-react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/navigation';
import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Skeleton } from '@/components/ui/skeleton';
import { usePaperCitationNetwork } from '@/lib/hooks/usePapers';
import { cn } from '@/lib/utils/cn';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });
const ForceGraph3D = dynamic(() => import('react-force-graph-3d'), { ssr: false });

interface CitationGraphProps {
  paperId: string;
  className?: string;
}

interface GraphNode {
  id: string;
  title: string;
  year: number | null;
  citations: number;
  impactScore: number;
  isCentral: boolean;
  val: number;
}

interface GraphLink {
  source: string;
  target: string;
}

const ESCAPE_MAP: Record<string, string> = {
  '&': '&amp;',
  '<': '&lt;',
  '>': '&gt;',
  '"': '&quot;',
  "'": '&#39;',
};

const escapeHtml = (value: unknown): string =>
  String(value).replace(/[&<>"']/g, (ch) => ESCAPE_MAP[ch] ?? ch);

function resolveThemeHex(varName: string, fallback: string): string {
  if (typeof window === 'undefined') return fallback;
  const raw = getComputedStyle(document.documentElement).getPropertyValue(varName).trim();
  if (!raw) return fallback;

  const isColorFunction = /^[a-z][a-z0-9-]*\(/i.test(raw);
  const isHex = raw.startsWith('#');
  const parts = raw.split(' ').filter(Boolean);

  let cssColor = raw;
  if (!isHex && !isColorFunction) {
    cssColor = parts.length >= 3 ? `hsl(${parts.join(' ')})` : `hsl(${raw})`;
  }

  const ctx = document.createElement('canvas').getContext('2d');
  if (!ctx) return fallback;
  ctx.fillStyle = fallback;
  ctx.fillStyle = cssColor;
  const normalized = ctx.fillStyle;
  return /^#[0-9a-f]{6}$/i.test(normalized) ? normalized : fallback;
}

export function CitationGraph({ paperId, className }: CitationGraphProps) {
  const router = useRouter();
  const { data, isLoading, error } = usePaperCitationNetwork(paperId);

  const [viewMode, setViewMode] = useState<'2d' | '3d'>('2d');
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  const [primaryColor] = useState(() => resolveThemeHex('--primary', '#e97316'));
  const containerRef = useRef<HTMLDivElement | null>(null);
  const observerRef = useRef<ResizeObserver | null>(null);
  // biome-ignore lint/suspicious/noExplicitAny: react-force-graph ref types are not exported
  const graph2DRef = useRef<any>(null);
  // biome-ignore lint/suspicious/noExplicitAny: react-force-graph ref types are not exported
  const graph3DRef = useRef<any>(null);

  const forcesConfigured = useRef(false);
  const initialFitDone = useRef(false);
  const hoveredNodeRef = useRef<string | null>(null);

  const setContainerRef = useCallback((el: HTMLDivElement | null) => {
    if (observerRef.current) {
      observerRef.current.disconnect();
      observerRef.current = null;
    }
    containerRef.current = el;
    if (!el) return;

    const { width, height } = el.getBoundingClientRect();
    if (width > 0 && height > 0) setDimensions({ width, height });

    observerRef.current = new ResizeObserver((entries) => {
      const entry = entries[0];
      if (!entry) return;
      const rect = entry.contentRect;
      if (rect.width > 0 && rect.height > 0) {
        setDimensions((prev) => {
          if (prev.width !== rect.width || prev.height !== rect.height) {
            return { width: rect.width, height: rect.height };
          }
          return prev;
        });
      }
    });
    observerRef.current.observe(el);
  }, []);

  const graphData = useMemo(() => {
    if (!data) return { nodes: [] as GraphNode[], links: [] as GraphLink[] };

    const nodes: GraphNode[] = data.papers.map((paper) => ({
      id: paper.paper_id,
      title: paper.title,
      year: paper.year,
      citations: paper.citations,
      impactScore: paper.impact_score ?? 0,
      isCentral: paper.paper_id === paperId,
      val: paper.paper_id === paperId ? 6 : 2 + (paper.impact_score ?? 0) / 10,
    }));

    const nodeIds = new Set(nodes.map((n) => n.id));
    const links: GraphLink[] = data.citations
      .filter((c) => nodeIds.has(c.source) && nodeIds.has(c.target))
      .map((c) => ({ source: c.source, target: c.target }));

    return { nodes, links };
  }, [data, paperId]);

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

  const handleNodeClick = useCallback(
    // biome-ignore lint/suspicious/noExplicitAny: node type from library
    (node: any) => {
      if (node?.id && node.id !== paperId) router.push(`/paper/${node.id}`);
    },
    [router, paperId],
  );

  const handleNodeHover = useCallback(
    // biome-ignore lint/suspicious/noExplicitAny: node type from library
    (node: any) => {
      const id = node?.id ?? null;
      hoveredNodeRef.current = id;
      if (viewMode === '2d') setHoveredNode(id);
    },
    [viewMode],
  );

  const handleEngineStop = useCallback(() => {
    if (initialFitDone.current) return;
    const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
    ref.current?.zoomToFit?.(400, 40);
    initialFitDone.current = true;
  }, [viewMode]);

  useEffect(() => {
    if (dimensions.width === 0 || dimensions.height === 0 || graphData.nodes.length === 0) return;
    const timer = setTimeout(() => {
      const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
      ref.current?.zoomToFit?.(400, 40);
    }, 300);
    return () => clearTimeout(timer);
  }, [dimensions.width, dimensions.height, viewMode, graphData.nodes.length]);

  // biome-ignore lint/correctness/useExhaustiveDependencies: graphData.nodes.length reconfigures forces when new data arrives
  useEffect(() => {
    forcesConfigured.current = false;
    initialFitDone.current = false;
    const interval = setInterval(() => {
      const ref = viewMode === '2d' ? graph2DRef : graph3DRef;
      if (ref.current && !forcesConfigured.current) {
        ref.current.d3Force?.('charge')?.strength?.(-300);
        ref.current.d3Force?.('link')?.distance?.(100);
        ref.current.d3Force?.('center')?.strength?.(1);
        ref.current.d3ReheatSimulation?.();
        forcesConfigured.current = true;
        clearInterval(interval);
      }
    }, 50);
    return () => clearInterval(interval);
  }, [viewMode, graphData.nodes.length]);

  const paintNode2D = useCallback(
    // biome-ignore lint/suspicious/noExplicitAny: node type from library
    (node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
      const isCentral = node.isCentral as boolean;
      const isHovered = hoveredNode === node.id;
      const isConnected = hoveredNode != null && adjacencyMap.get(hoveredNode)?.has(node.id);
      const isDimmed = hoveredNode != null && !isHovered && !isConnected && !isCentral;

      const radius = Math.sqrt(node.val || 1) * 4;
      const x = node.x ?? 0;
      const y = node.y ?? 0;

      // Glow
      if (!isDimmed) {
        const glowRadius = radius * (isHovered || isCentral ? 3 : 2);
        const glowAlpha = isHovered ? '60' : isCentral ? '40' : '25';
        const gradient = ctx.createRadialGradient(x, y, radius * 0.3, x, y, glowRadius);
        gradient.addColorStop(0, `${primaryColor}${glowAlpha}`);
        gradient.addColorStop(1, `${primaryColor}00`);
        ctx.beginPath();
        ctx.arc(x, y, glowRadius, 0, 2 * Math.PI);
        ctx.fillStyle = gradient;
        ctx.fill();
      }

      // Circle
      ctx.beginPath();
      ctx.arc(x, y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = isDimmed ? `${primaryColor}35` : isCentral ? '#f97316' : primaryColor;
      ctx.fill();

      // Ring on central node or hover
      if (isCentral || isHovered) {
        ctx.strokeStyle = isCentral ? 'rgba(249, 115, 22, 0.9)' : 'rgba(255,255,255,0.8)';
        ctx.lineWidth = (isCentral ? 2.5 : 1.5) / globalScale;
        ctx.stroke();
      }

      // Label
      if (globalScale > 0.7 && !isDimmed) {
        const label = node.title.length > 28 ? `${node.title.slice(0, 28)}...` : node.title;
        const fontSize = Math.max(11 / globalScale, 2.5);
        ctx.font = `${isCentral ? '800' : '600'} ${fontSize}px "JetBrains Mono", monospace`;
        ctx.textAlign = 'center';
        ctx.textBaseline = 'top';
        ctx.fillStyle = isCentral || isHovered ? 'rgba(255,255,255,1)' : 'rgba(255,255,255,0.75)';
        ctx.fillText(label, x, y + radius + 3 / globalScale);
      }
    },
    [hoveredNode, adjacencyMap, primaryColor],
  );

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

  const getLinkColor = useCallback(
    (link: Record<string, unknown>) => {
      if (!hoveredNode) return 'rgba(255, 255, 255, 0.12)';
      const src =
        typeof link.source === 'string' ? link.source : (link.source as { id: string })?.id;
      const tgt =
        typeof link.target === 'string' ? link.target : (link.target as { id: string })?.id;
      if (src === hoveredNode || tgt === hoveredNode) return `${primaryColor}bb`;
      return 'rgba(255, 255, 255, 0.04)';
    },
    [hoveredNode, primaryColor],
  );

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

  const getNodeTooltip = useCallback(
    // biome-ignore lint/suspicious/noExplicitAny: node type from library
    (node: any) => {
      const title = escapeHtml(node.title ?? 'Untitled');
      const year = escapeHtml(node.year ?? 'N/A');
      const citations = Number(node.citations ?? 0);
      const impact = Number(node.impactScore ?? 0).toFixed(1);
      const central = node.isCentral
        ? '<div style="color:#f97316;font-size:9px;font-weight:900;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">Current Paper</div>'
        : '';
      return `<div style="background:rgba(10,10,18,0.95);border:1px solid rgba(255,255,255,0.12);border-radius:10px;padding:10px 14px;font-family:'JetBrains Mono',monospace;max-width:300px;backdrop-filter:blur(8px)">
      ${central}<div style="font-weight:900;font-size:12px;color:white;line-height:1.3">${title}</div>
      <div style="color:rgba(255,255,255,0.5);font-size:10px;margin-top:6px;font-weight:600;letter-spacing:0.05em;text-transform:uppercase">${year} &middot; ${citations} citations &middot; Impact ${impact}</div>
    </div>`;
    },
    [],
  );

  const frameClass = cn('h-[500px] w-full rounded-3xl', className);

  if (isLoading) {
    return (
      <div
        className={cn(
          frameClass,
          'bg-muted/20 flex flex-col items-center justify-center space-y-4',
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

  if (graphData.nodes.length === 0) {
    return (
      <div className={cn(frameClass, 'flex items-center justify-center bg-secondary/10 border')}>
        <span className="text-muted-foreground font-bold uppercase text-xs tracking-widest">
          No citation network data available
        </span>
      </div>
    );
  }

  const sharedProps = {
    graphData,
    width: dimensions.width,
    height: dimensions.height,
    nodeId: 'id' as const,
    nodeVal: 'val' as const,
    nodeLabel: getNodeTooltip,
    linkCurvature: 0.15,
    linkDirectionalParticles: 2,
    linkDirectionalParticleSpeed: 0.005,
    linkDirectionalParticleWidth: 1.5,
    linkDirectionalParticleColor: () => `${primaryColor}cc`,
    onNodeClick: handleNodeClick,
    onNodeHover: handleNodeHover,
    onEngineStop: handleEngineStop,
    backgroundColor: 'rgba(0,0,0,0)',
    warmupTicks: 0,
    cooldownTime: 4000,
    d3VelocityDecay: 0.3,
  };

  return (
    <div
      ref={setContainerRef}
      className={cn(
        'relative h-[500px] w-full border rounded-3xl overflow-hidden bg-card/50 backdrop-blur-sm',
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

      {/* Zoom Controls */}
      <div className="absolute bottom-4 left-4 z-10 flex flex-col gap-1 p-1.5 rounded-xl bg-card/90 border border-border shadow-lg backdrop-blur-sm">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomIn}
          aria-label="Zoom in"
          className="h-7 w-7 text-foreground hover:text-primary hover:bg-primary/10"
        >
          <Plus className="h-3.5 w-3.5" />
        </Button>
        <Button
          variant="ghost"
          size="icon"
          onClick={handleZoomOut}
          aria-label="Zoom out"
          className="h-7 w-7 text-foreground hover:text-primary hover:bg-primary/10"
        >
          <Minus className="h-3.5 w-3.5" />
        </Button>
        <div className="h-px bg-border mx-1" />
        <Button
          variant="ghost"
          size="icon"
          onClick={handleFit}
          aria-label="Fit to view"
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

      {viewMode === '3d' && dimensions.width > 0 && (
        <ForceGraph3D
          ref={graph3DRef}
          {...sharedProps}
          nodeColor={(node: Record<string, unknown>) => {
            const nodeId = node.id as string;
            const isCentral = node.isCentral as boolean;
            const hovered = hoveredNodeRef.current;
            if (isCentral) return '#f97316';
            if (!hovered) return primaryColor;
            if (nodeId === hovered) return primaryColor;
            if (adjacencyMap.get(hovered)?.has(nodeId)) return primaryColor;
            return `${primaryColor}50`;
          }}
          nodeOpacity={0.9}
          linkColor={(link: Record<string, unknown>) => {
            const hovered = hoveredNodeRef.current;
            if (!hovered) return 'rgba(255, 255, 255, 0.12)';
            const src =
              typeof link.source === 'string' ? link.source : (link.source as { id: string })?.id;
            const tgt =
              typeof link.target === 'string' ? link.target : (link.target as { id: string })?.id;
            if (src === hovered || tgt === hovered) return `${primaryColor}bb`;
            return 'rgba(255, 255, 255, 0.04)';
          }}
          linkWidth={(link: Record<string, unknown>) => {
            const hovered = hoveredNodeRef.current;
            if (!hovered) return 0.5;
            const src =
              typeof link.source === 'string' ? link.source : (link.source as { id: string })?.id;
            const tgt =
              typeof link.target === 'string' ? link.target : (link.target as { id: string })?.id;
            return src === hovered || tgt === hovered ? 2 : 0.2;
          }}
          linkOpacity={0.3}
          showNavInfo={false}
          enableNavigationControls
        />
      )}
    </div>
  );
}
