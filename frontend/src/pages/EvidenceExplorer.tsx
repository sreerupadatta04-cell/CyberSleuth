import React, { useEffect, useState, useRef } from 'react';
import {
  Network,
  ZoomIn,
  ZoomOut,
  RotateCcw,
  Filter,
  User,
  Server,
  Globe,
  Terminal,
  ShieldAlert,
  Search,
  Activity,
  Layers,
  Info,
  CheckCircle2,
  X
} from 'lucide-react';
import { fetchEvidenceGraph, fetchInvestigations } from '../services/api';
import { EvidenceGraphData, GraphNode, GraphEdge, Investigation } from '../types';
import { ProvenanceBadge } from '../components/common/Badge';
import { EmptyState } from '../components/common/EmptyState';

interface EvidenceExplorerProps {
  initialInvestigationId?: string | null;
}

export const EvidenceExplorer: React.FC<EvidenceExplorerProps> = ({ initialInvestigationId }) => {
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [selectedInvId, setSelectedInvId] = useState<string>(initialInvestigationId || '');
  const [graphData, setGraphData] = useState<EvidenceGraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  // Filters
  const [filterType, setFilterType] = useState<string>('ALL');

  // Zoom & Pan
  const [zoom, setZoom] = useState<number>(1);
  const [pan, setPan] = useState<{ x: number; y: number }>({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState<boolean>(false);
  const [dragStart, setDragStart] = useState<{ x: number; y: number }>({ x: 0, y: 0 });

  useEffect(() => {
    async function init() {
      try {
        setLoading(true);
        const invs = await fetchInvestigations();
        setInvestigations(invs);
        if (initialInvestigationId) {
          setSelectedInvId(initialInvestigationId);
        } else if (invs.length > 0) {
          setSelectedInvId(invs[0].id);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    init();
  }, [initialInvestigationId]);

  useEffect(() => {
    if (!selectedInvId) return;
    async function loadGraph() {
      try {
        setLoading(true);
        const data = await fetchEvidenceGraph(selectedInvId);
        setGraphData(data);
        if (data.nodes.length > 0) {
          setSelectedNode(data.nodes[0]);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    loadGraph();
  }, [selectedInvId]);

  // Compute node positions in SVG viewport
  const width = 860;
  const height = 580;
  const centerX = width / 2;
  const centerY = height / 2;

  const nodePositions = React.useMemo(() => {
    if (!graphData || graphData.nodes.length === 0) return {};
    const pos: Record<string, { x: number; y: number }> = {};
    const nodes = graphData.nodes;

    // Center the investigation node
    const invNode = nodes.find((n) => n.node_type === 'investigation');
    if (invNode) pos[invNode.id] = { x: centerX, y: centerY };

    // Group other nodes into concentric rings
    const otherNodes = nodes.filter((n) => n.node_type !== 'investigation');
    const ring1 = otherNodes.filter((n) => n.node_type === 'alert' || n.node_type === 'host' || n.node_type === 'user');
    const ring2 = otherNodes.filter((n) => !ring1.includes(n));

    // Place ring 1
    const r1 = 170;
    ring1.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / ring1.length;
      pos[n.id] = {
        x: centerX + r1 * Math.cos(angle),
        y: centerY + r1 * Math.sin(angle),
      };
    });

    // Place ring 2
    const r2 = 280;
    ring2.forEach((n, i) => {
      const angle = (2 * Math.PI * i) / Math.max(ring2.length, 1) + 0.3;
      pos[n.id] = {
        x: centerX + r2 * Math.cos(angle),
        y: centerY + r2 * Math.sin(angle),
      };
    });

    return pos;
  }, [graphData]);

  const getNodeColor = (type: string) => {
    switch (type) {
      case 'user':
        return '#FFB454'; // Amber
      case 'host':
        return '#00D5C5'; // Cyan
      case 'ip':
        return '#B6FF5C'; // Lime
      case 'process':
        return '#FF626C'; // Coral
      case 'domain':
        return '#91AAA5'; // Sage
      case 'alert':
        return '#FF626C'; // Coral
      case 'event':
        return '#055861'; // Deep Teal
      case 'investigation':
        return '#00D5C5'; // Neon Cyan
      default:
        return '#033C42';
    }
  };

  const handleMouseDown = (e: React.MouseEvent) => {
    setIsDragging(true);
    setDragStart({ x: e.clientX - pan.x, y: e.clientY - pan.y });
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setPan({ x: e.clientX - dragStart.x, y: e.clientY - dragStart.y });
    }
  };

  const handleMouseUp = () => setIsDragging(false);

  const filteredNodes = (graphData?.nodes || []).filter(
    (n) => filterType === 'ALL' || n.node_type === filterType.toLowerCase()
  );

  return (
    <div className="p-6 space-y-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-teal-light/40 gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Network className="w-5 h-5 text-cyan-neon" />
            <h1 className="text-xl md:text-2xl font-bold font-heading tracking-tight text-ivory">
              EVIDENCE CORRELATION GRAPH
            </h1>
          </div>
          <p className="text-xs font-mono text-sage mt-1">
            Interactive Forensic Topology • Grounded Distinctions: OBSERVED vs INFERRED
          </p>
        </div>

        {/* Investigation Switcher */}
        <div className="flex items-center space-x-2">
          <span className="text-xs font-mono text-sage">INVESTIGATION:</span>
          <select
            value={selectedInvId}
            onChange={(e) => setSelectedInvId(e.target.value)}
            className="bg-charcoal border border-cyan-neon/40 rounded px-2.5 py-1.5 font-mono text-xs text-cyan-neon focus:outline-none"
          >
            {investigations.map((i) => (
              <option key={i.id} value={i.id}>
                {i.id} - Alert {i.alert_id}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Control Bar & Legend */}
      <div className="flex flex-wrap items-center justify-between p-3 rounded-lg bg-charcoal border border-teal-light/30 gap-3 text-xs font-mono">
        {/* Node Filters */}
        <div className="flex items-center space-x-2">
          <Filter className="w-3.5 h-3.5 text-sage" />
          <span className="text-sage">FILTER ENTITY:</span>
          <select
            value={filterType}
            onChange={(e) => setFilterType(e.target.value)}
            className="bg-obsidian border border-teal-light/40 rounded px-2 py-1 text-ivory text-xs focus:outline-none"
          >
            <option value="ALL">All Entities ({graphData?.nodes.length || 0})</option>
            <option value="USER">Users</option>
            <option value="HOST">Hosts</option>
            <option value="IP">IP Addresses</option>
            <option value="PROCESS">Processes</option>
            <option value="EVENT">Events</option>
            <option value="ALERT">Alerts</option>
          </select>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-4 text-[11px]">
          <div className="flex items-center space-x-1">
            <span className="w-3 h-0.5 bg-cyan-neon" />
            <span className="text-cyan-neon font-bold">OBSERVED LINK</span>
          </div>
          <div className="flex items-center space-x-1">
            <span className="w-3 h-0.5 border-b border-dashed border-amber-neon" />
            <span className="text-amber-neon font-bold">INFERRED LINK</span>
          </div>
          <div className="flex items-center space-x-1.5 text-sage">
            <span className="w-2.5 h-2.5 rounded-full bg-[#00D5C5]" />
            <span>Host</span>
          </div>
          <div className="flex items-center space-x-1.5 text-sage">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FFB454]" />
            <span>User</span>
          </div>
          <div className="flex items-center space-x-1.5 text-sage">
            <span className="w-2.5 h-2.5 rounded-full bg-[#B6FF5C]" />
            <span>IP</span>
          </div>
          <div className="flex items-center space-x-1.5 text-sage">
            <span className="w-2.5 h-2.5 rounded-full bg-[#FF626C]" />
            <span>Process</span>
          </div>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center space-x-1">
          <button
            onClick={() => setZoom((z) => Math.min(z + 0.2, 2.5))}
            className="p-1 rounded bg-obsidian border border-teal-light text-sage hover:text-cyan-neon"
            title="Zoom In"
          >
            <ZoomIn className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => setZoom((z) => Math.max(z - 0.2, 0.4))}
            className="p-1 rounded bg-obsidian border border-teal-light text-sage hover:text-cyan-neon"
            title="Zoom Out"
          >
            <ZoomOut className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={() => {
              setZoom(1);
              setPan({ x: 0, y: 0 });
            }}
            className="p-1 rounded bg-obsidian border border-teal-light text-sage hover:text-cyan-neon"
            title="Reset Pan/Zoom"
          >
            <RotateCcw className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>

      {/* Main Canvas + Detail Drawer */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-4">
        {/* SVG Graph Viewport */}
        <div
          className="lg:col-span-8 h-[600px] rounded-lg bg-obsidian border border-teal-light/40 relative overflow-hidden select-none cursor-grab active:cursor-grabbing bg-tech-grid"
          onMouseDown={handleMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          {loading && (
            <div className="absolute inset-0 flex items-center justify-center bg-obsidian/70 font-mono text-cyan-neon text-xs">
              <Activity className="w-4 h-4 mr-2 animate-spin" />
              RENDERING FORENSIC TOPOLOGY...
            </div>
          )}

          <svg
            width="100%"
            height="100%"
            viewBox={`0 0 ${width} ${height}`}
            className="w-full h-full"
          >
            <defs>
              <marker
                id="arrow-observed"
                viewBox="0 0 10 10"
                refX="20"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#00D5C5" />
              </marker>
              <marker
                id="arrow-inferred"
                viewBox="0 0 10 10"
                refX="20"
                refY="5"
                markerWidth="6"
                markerHeight="6"
                orient="auto-start-reverse"
              >
                <path d="M 0 0 L 10 5 L 0 10 z" fill="#FFB454" />
              </marker>
            </defs>

            <g
              transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}
              style={{ transformOrigin: 'center' }}
            >
              {/* EDGES */}
              {(graphData?.edges || []).map((edge) => {
                const src = nodePositions[edge.source];
                const dst = nodePositions[edge.target];
                if (!src || !dst) return null;

                const isInferred = edge.relationship_category === 'INFERRED';
                const strokeColor = isInferred ? '#FFB454' : '#00D5C5';

                return (
                  <g key={edge.id} className="transition-opacity">
                    <line
                      x1={src.x}
                      y1={src.y}
                      x2={dst.x}
                      y2={dst.y}
                      stroke={strokeColor}
                      strokeWidth={isInferred ? 1.5 : 1.8}
                      strokeDasharray={isInferred ? '5,5' : 'none'}
                      strokeOpacity={0.65}
                      markerEnd={isInferred ? 'url(#arrow-inferred)' : 'url(#arrow-observed)'}
                    />
                    {/* Relationship label in midpoint */}
                    <text
                      x={(src.x + dst.x) / 2}
                      y={(src.y + dst.y) / 2 - 4}
                      fill={strokeColor}
                      fontSize="9"
                      fontFamily="IBM Plex Mono"
                      textAnchor="middle"
                      className="select-none pointer-events-none opacity-80"
                    >
                      {edge.relationship_type}
                    </text>
                  </g>
                );
              })}

              {/* NODES */}
              {filteredNodes.map((node) => {
                const pos = nodePositions[node.id];
                if (!pos) return null;

                const isSelected = selectedNode?.id === node.id;
                const isHovered = hoveredNode?.id === node.id;
                const color = getNodeColor(node.node_type);
                const radius = node.node_type === 'investigation' ? 24 : 18;

                return (
                  <g
                    key={node.id}
                    transform={`translate(${pos.x}, ${pos.y})`}
                    onClick={(e) => {
                      e.stopPropagation();
                      setSelectedNode(node);
                    }}
                    onMouseEnter={() => setHoveredNode(node)}
                    onMouseLeave={() => setHoveredNode(null)}
                    className="cursor-pointer"
                  >
                    {/* Glowing outer halo if selected */}
                    {isSelected && (
                      <circle
                        r={radius + 8}
                        fill="none"
                        stroke={color}
                        strokeWidth="2"
                        strokeDasharray="4,4"
                        className="animate-spin"
                        style={{ transformOrigin: 'center' }}
                      />
                    )}

                    {/* Main Node Body */}
                    <circle
                      r={radius}
                      fill="#101C1D"
                      stroke={color}
                      strokeWidth={isSelected ? 3 : 2}
                      className="transition-all"
                    />

                    {/* Node Label Below */}
                    <text
                      y={radius + 14}
                      fill="#E7F0EC"
                      fontSize="10"
                      fontFamily="IBM Plex Mono"
                      textAnchor="middle"
                      className="font-bold select-none pointer-events-none"
                    >
                      {node.label}
                    </text>

                    {/* Category tag */}
                    <text
                      y={radius + 24}
                      fill={color}
                      fontSize="8"
                      fontFamily="IBM Plex Mono"
                      textAnchor="middle"
                      className="select-none pointer-events-none opacity-70"
                    >
                      {node.node_type.toUpperCase()}
                    </text>
                  </g>
                );
              })}
            </g>
          </svg>

          {/* Canvas Stats Overlay */}
          <div className="absolute bottom-3 left-3 px-3 py-1.5 rounded bg-charcoal/90 border border-teal-light/30 text-[10px] font-mono text-sage flex items-center space-x-3 pointer-events-none">
            <span>Nodes: <strong className="text-cyan-neon">{graphData?.stats.total_nodes || 0}</strong></span>
            <span>•</span>
            <span>Edges: <strong className="text-cyan-neon">{graphData?.stats.total_edges || 0}</strong></span>
            <span>•</span>
            <span>Observed: <strong className="text-cyan-neon">{graphData?.stats.observed_count || 0}</strong></span>
            <span>•</span>
            <span>Inferred: <strong className="text-amber-neon">{graphData?.stats.inferred_count || 0}</strong></span>
          </div>
        </div>

        {/* Selected Entity Inspection Drawer */}
        <div className="lg:col-span-4 p-5 rounded-lg bg-charcoal border border-cyan-neon/30 flex flex-col space-y-4">
          <div className="flex items-center justify-between pb-3 border-b border-teal-light/30">
            <span className="text-xs font-mono font-bold text-cyan-neon uppercase tracking-wider flex items-center">
              <Info className="w-3.5 h-3.5 mr-1" />
              Node Forensic Inspector
            </span>
            {selectedNode && (
              <span className="text-[10px] font-mono px-2 py-0.5 rounded border border-teal-light text-sage uppercase">
                {selectedNode.node_type}
              </span>
            )}
          </div>

          {selectedNode ? (
            <div className="space-y-4 font-mono text-xs">
              <div>
                <div className="text-[10px] text-sage uppercase">Entity Identifier</div>
                <div className="text-base font-bold text-ivory break-all">
                  {selectedNode.id}
                </div>
              </div>

              <div>
                <div className="text-[10px] text-sage uppercase">Display Name</div>
                <div className="text-sm font-semibold text-cyan-neon">
                  {selectedNode.label}
                </div>
              </div>

              <div className="p-3 rounded bg-obsidian/70 border border-teal-light/30 space-y-1.5">
                <div className="text-[10px] text-sage uppercase">Provenance Category</div>
                <div>
                  <ProvenanceBadge category={selectedNode.category} />
                </div>
              </div>

              {/* Attributes / Metadata */}
              <div>
                <div className="text-[10px] text-sage uppercase mb-1">Entity Attributes</div>
                <div className="p-3 rounded bg-obsidian/70 border border-teal-light/30 max-h-48 overflow-y-auto space-y-1">
                  {Object.entries(selectedNode.details || {}).map(([k, v]) => (
                    <div key={k} className="flex justify-between text-[11px]">
                      <span className="text-sage truncate mr-2">{k}:</span>
                      <span className="text-ivory font-bold truncate max-w-[180px]">
                        {String(v)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Connected Relationships */}
              <div>
                <div className="text-[10px] text-sage uppercase mb-1">Adjacent Linkages</div>
                <div className="space-y-1.5 max-h-40 overflow-y-auto">
                  {(graphData?.edges || [])
                    .filter((e) => e.source === selectedNode.id || e.target === selectedNode.id)
                    .map((e) => (
                      <div
                        key={e.id}
                        className="p-2 rounded bg-obsidian/50 border border-teal-light/20 text-[10px] flex items-center justify-between"
                      >
                        <span className="text-ivory">{e.relationship_type}</span>
                        <span
                          className={`font-bold ${
                            e.relationship_category === 'INFERRED' ? 'text-amber-neon' : 'text-cyan-neon'
                          }`}
                        >
                          {e.relationship_category}
                        </span>
                      </div>
                    ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="py-16 text-center text-xs font-mono text-sage">
              Click any node in the evidence graph to inspect its forensic provenance and linkages.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
