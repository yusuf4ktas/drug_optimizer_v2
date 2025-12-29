import React, { useState, useEffect, useRef } from 'react';
import { ZoomIn, ZoomOut, Move, RefreshCcw } from 'lucide-react';

export default function InteractiveGraph({ data, height = 800 }) {
  // --- State ---
  const [nodes, setNodes] = useState([]);
  const [links, setLinks] = useState([]);
  const [transform, setTransform] = useState({ x: 0, y: 0, k: 0.8 });
  const [hoveredNode, setHoveredNode] = useState(null);
  const [draggingNode, setDraggingNode] = useState(null);

  const svgRef = useRef(null);

  const width = 1000;
  const drugRadius = 300;
  const condRadius = 80;

  useEffect(() => {
    if (!data || !data.nodes || data.nodes.length === 0) return;

    const centerX = width / 2;
    const centerY = height / 2;

    const conditions = data.nodes.filter(n => n.group === 'condition');
    const drugs = data.nodes.filter(n => n.group === 'drug');

    // Position Conditions (Center)
    const processedConditions = conditions.map((node, i) => {
      const angle = (i / conditions.length) * 2 * Math.PI;
      const r = conditions.length === 1 ? 0 : condRadius;
      return {
        ...node,
        x: centerX + r * Math.cos(angle),
        y: centerY + r * Math.sin(angle),
        color: '#0f172a',
        radius: 20
      };
    });

    // Position Drugs (Outer Circle)
    const processedDrugs = drugs.map((node, i) => {
      const stagger = i % 2 === 0 ? 0 : 30;
      const angle = (i / drugs.length) * 2 * Math.PI;
      return {
        ...node,
        x: centerX + (drugRadius + stagger) * Math.cos(angle),
        y: centerY + (drugRadius + stagger) * Math.sin(angle),
        color: '#10b981',
        radius: 8
      };
    });

    const allNodes = [...processedConditions, ...processedDrugs];
    setNodes(allNodes);

    // Map Links
    const processedLinks = data.links.map(link => {
      const sourceId = typeof link.source === 'object' ? link.source.id : link.source;
      const targetId = typeof link.target === 'object' ? link.target.id : link.target;
      return { source: sourceId, target: targetId };
    });
    setLinks(processedLinks);

  }, [data, height]);

  // --- Interaction Handlers ---

  const handleZoom = (delta) => {
    setTransform(prev => ({
      ...prev,
      k: Math.max(0.2, Math.min(4, prev.k + delta))
    }));
  };

  const handleMouseDown = (e, node) => {
    e.stopPropagation();
    setDraggingNode(node.id);
  };

  const handleMouseMove = (e) => {
    if (draggingNode) {
      if (svgRef.current) {
        const CTM = svgRef.current.getScreenCTM();
        const mouseX = (e.clientX - CTM.e) / CTM.a;
        const mouseY = (e.clientY - CTM.f) / CTM.d;

        const finalX = (mouseX - transform.x) / transform.k;
        const finalY = (mouseY - transform.y) / transform.k;

        setNodes(prev => prev.map(n =>
          n.id === draggingNode ? { ...n, x: finalX, y: finalY } : n
        ));
      }
    }
  };

  const handleMouseUp = () => {
    setDraggingNode(null);
  };

  const isConnected = (n1, n2) => {
    return links.some(l =>
      (l.source === n1.id && l.target === n2.id) ||
      (l.source === n2.id && l.target === n1.id)
    );
  };

  if (!nodes.length) return null;

  return (
    <div className="w-full flex flex-col items-center bg-white rounded-2xl border border-slate-200 shadow-xl overflow-hidden relative">

      {/* Toolbar */}
      <div className="absolute top-4 right-4 flex flex-col gap-2 bg-white/90 p-2 rounded-lg shadow border border-slate-100 z-10">
        <button onClick={() => handleZoom(0.2)} className="p-2 hover:bg-slate-100 rounded text-slate-600" title="Zoom In"><ZoomIn size={18}/></button>
        <button onClick={() => handleZoom(-0.2)} className="p-2 hover:bg-slate-100 rounded text-slate-600" title="Zoom Out"><ZoomOut size={18}/></button>
        <button onClick={() => setTransform({x:0, y:0, k:0.8})} className="p-2 hover:bg-slate-100 rounded text-slate-600" title="Reset"><RefreshCcw size={18}/></button>
      </div>

      <div className="absolute top-4 left-4 bg-white/80 p-3 rounded-lg text-xs font-mono text-slate-500 pointer-events-none z-10">
         <div className="font-bold text-slate-800 mb-1">INTERACTIVE MODE</div>
         <div>• Drag nodes</div>
         <div>• Hover to focus</div>
         <div>• Scroll to zoom</div>
      </div>

      {/* Main SVG Canvas */}
      <svg
        ref={svgRef}
        width="100%"
        height={height}
        className="cursor-move bg-slate-50/30"
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={(e) => handleZoom(e.deltaY * -0.001)}
      >
        <g transform={`translate(${transform.x},${transform.y}) scale(${transform.k})`}>

          {/* Links */}
          {links.map((link, i) => {
            const sourceNode = nodes.find(n => n.id === link.source);
            const targetNode = nodes.find(n => n.id === link.target);
            if (!sourceNode || !targetNode) return null;

            const isDimmed = hoveredNode &&
              link.source !== hoveredNode &&
              link.target !== hoveredNode;

            return (
              <line
                key={i}
                x1={sourceNode.x}
                y1={sourceNode.y}
                x2={targetNode.x}
                y2={targetNode.y}
                stroke={isDimmed ? "#e2e8f0" : "#cbd5e1"}
                strokeWidth={isDimmed ? 1 : 2}
                strokeOpacity={isDimmed ? 0.2 : 0.6}
                className="transition-all duration-300"
              />
            );
          })}

          {/* Nodes */}
          {nodes.map((node, i) => {
            const isDimmed = hoveredNode && hoveredNode !== node.id && !isConnected(node, { id: hoveredNode });
            const isHovered = hoveredNode === node.id;

            return (
              <g
                key={i}
                className="transition-opacity duration-300 cursor-grab active:cursor-grabbing"
                onMouseEnter={() => setHoveredNode(node.id)}
                onMouseLeave={() => setHoveredNode(null)}
                onMouseDown={(e) => handleMouseDown(e, node)}
                style={{ opacity: isDimmed ? 0.1 : 1 }}
              >
                {/* Glow */}
                {isHovered && <circle cx={node.x} cy={node.y} r={node.radius + 10} fill={node.color} opacity="0.2" />}

                <circle
                  cx={node.x}
                  cy={node.y}
                  r={node.radius}
                  fill={node.color}
                  className="drop-shadow-sm"
                />

                {(node.group === 'condition' || isHovered || (!hoveredNode && transform.k > 1.2)) && (
                   <text
                    x={node.x}
                    y={node.y - (node.radius + 10)}
                    textAnchor="middle"
                    className={`
                      text-[12px] font-bold uppercase pointer-events-none select-none
                      ${node.group === 'condition' ? 'fill-slate-900 text-sm' : 'fill-slate-600'}
                    `}
                    style={{ textShadow: '0px 2px 4px rgba(255,255,255,1)' }}
                  >
                    {node.name.length > 25 && !isHovered ? node.name.substring(0, 23) + '...' : node.name}
                  </text>
                )}
              </g>
            );
          })}
        </g>
      </svg>
    </div>
  );
}