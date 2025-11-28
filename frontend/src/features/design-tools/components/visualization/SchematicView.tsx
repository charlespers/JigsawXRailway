/**
 * Schematic View Component
 * Interactive schematic representation of the design
 */

import React, { useState, useMemo } from "react";
import { Card } from "../../shared/components/ui/card";
import { Button } from "../../shared/components/ui/button";
import { Badge } from "../../shared/components/ui/badge";
import {
  ZoomIn,
  ZoomOut,
  Maximize2,
  Search,
  Layers,
  Settings,
} from "lucide-react";
import type { PartObject } from "../../shared/services/types";

interface SchematicViewProps {
  parts: PartObject[];
  connections?: any[];
  onPartClick?: (part: PartObject) => void;
}

interface ComponentNode {
  id: string;
  part: PartObject;
  position: { x: number; y: number };
  connections: string[];
}

export default function SchematicView({
  parts,
  connections = [],
  onPartClick,
}: SchematicViewProps) {
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [selectedPart, setSelectedPart] = useState<string | null>(null);
  const [showLabels, setShowLabels] = useState(true);

  // Organize components into a schematic layout
  const componentNodes = useMemo(() => {
    const nodes: ComponentNode[] = [];
    const gridSize = Math.ceil(Math.sqrt(parts.length));
    const spacing = 200;

    parts.forEach((part, index) => {
      const row = Math.floor(index / gridSize);
      const col = index % gridSize;
      
      // Get connections for this part
      const partConnections = connections
        .filter(conn => 
          conn.components?.includes(part.componentId) ||
          conn.components?.includes(part.mpn)
        )
        .map(conn => conn.net_name);

      nodes.push({
        id: part.componentId,
        part,
        position: {
          x: col * spacing + 100,
          y: row * spacing + 100,
        },
        connections: partConnections,
      });
    });

    return nodes;
  }, [parts, connections]);

  const handleZoomIn = () => setZoom(prev => Math.min(prev + 0.1, 3));
  const handleZoomOut = () => setZoom(prev => Math.max(prev - 0.1, 0.5));
  const handleReset = () => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  };

  return (
    <Card className="bg-dark-surface border-dark-border p-4">
      {/* Toolbar */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <h3 className="text-lg font-semibold text-white">Schematic View</h3>
          <Badge variant="outline" className="text-xs">
            {parts.length} components
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={() => setShowLabels(!showLabels)}
            className="text-xs"
          >
            <Layers className="w-4 h-4 mr-1" />
            {showLabels ? "Hide" : "Show"} Labels
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleZoomOut}
            className="text-xs"
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-xs text-neutral-blue min-w-[3rem] text-center">
            {(zoom * 100).toFixed(0)}%
          </span>
          <Button
            size="sm"
            variant="outline"
            onClick={handleZoomIn}
            className="text-xs"
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
          <Button
            size="sm"
            variant="outline"
            onClick={handleReset}
            className="text-xs"
          >
            <Maximize2 className="w-4 h-4" />
          </Button>
        </div>
      </div>

      {/* Schematic Canvas */}
      <div
        className="relative border border-dark-border rounded bg-dark-bg overflow-auto"
        style={{ height: "600px" }}
      >
        <svg
          width="100%"
          height="100%"
          style={{
            transform: `translate(${pan.x}px, ${pan.y}px) scale(${zoom})`,
            transformOrigin: "0 0",
          }}
        >
          {/* Draw connections */}
          <g className="connections">
            {connections.map((conn, idx) => {
              const compIds = conn.components || [];
              const connectedNodes = componentNodes.filter(node =>
                compIds.includes(node.id) || compIds.includes(node.part.mpn)
              );
              
              if (connectedNodes.length < 2) return null;
              
              const [node1, node2] = connectedNodes;
              return (
                <line
                  key={idx}
                  x1={node1.position.x}
                  y1={node1.position.y}
                  x2={node2.position.x}
                  y2={node2.position.y}
                  stroke="#10b981"
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  opacity="0.5"
                />
              );
            })}
          </g>

          {/* Draw components */}
          <g className="components">
            {componentNodes.map((node) => (
              <g key={node.id}>
                {/* Component box */}
                <rect
                  x={node.position.x - 40}
                  y={node.position.y - 30}
                  width="80"
                  height="60"
                  fill={selectedPart === node.id ? "#10b981" : "#1f2937"}
                  stroke={selectedPart === node.id ? "#10b981" : "#374151"}
                  strokeWidth="2"
                  rx="4"
                  onClick={() => {
                    setSelectedPart(node.id);
                    onPartClick?.(node.part);
                  }}
                  className="cursor-pointer hover:stroke-neon-teal transition-colors"
                />
                
                {/* Component label */}
                {showLabels && (
                  <>
                    <text
                      x={node.position.x}
                      y={node.position.y - 10}
                      textAnchor="middle"
                      fill="#ffffff"
                      fontSize="10"
                      fontWeight="bold"
                      className="pointer-events-none"
                    >
                      {node.part.mpn.split("-")[0] || node.part.componentId}
                    </text>
                    <text
                      x={node.position.x}
                      y={node.position.y + 5}
                      textAnchor="middle"
                      fill="#9ca3af"
                      fontSize="8"
                      className="pointer-events-none"
                    >
                      {node.part.manufacturer}
                    </text>
                    <text
                      x={node.position.x}
                      y={node.position.y + 20}
                      textAnchor="middle"
                      fill="#6b7280"
                      fontSize="8"
                      className="pointer-events-none"
                    >
                      {node.part.package || ""}
                    </text>
                  </>
                )}
              </g>
            ))}
          </g>
        </svg>
      </div>

      {/* Component Info */}
      {selectedPart && (
        <div className="mt-4 p-3 bg-zinc-900/50 rounded border border-dark-border">
          {(() => {
            const part = parts.find(p => p.componentId === selectedPart);
            if (!part) return null;
            return (
              <div>
                <div className="text-sm font-medium text-white mb-2">
                  {part.mpn} - {part.manufacturer}
                </div>
                <div className="text-xs text-neutral-blue space-y-1">
                  <div>Description: {part.description}</div>
                  {part.voltage && <div>Voltage: {part.voltage}</div>}
                  {part.package && <div>Package: {part.package}</div>}
                  {part.interfaces && part.interfaces.length > 0 && (
                    <div>Interfaces: {part.interfaces.join(", ")}</div>
                  )}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </Card>
  );
}

