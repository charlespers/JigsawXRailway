/**
 * Netlist View Component
 * Visualize netlist and connections
 */

import React, { useMemo, useState } from "react";
import { Card } from "../../ui/card";
import { Badge } from "../../ui/badge";
import { Button } from "../../ui/button";
import {
  Network,
  Search,
  Filter,
  Download,
  Copy,
  Eye,
  EyeOff,
} from "lucide-react";
import type { PartObject } from "../../services/types";

interface NetlistViewProps {
  parts: PartObject[];
  connections: any[];
  onNetClick?: (netName: string) => void;
}

interface NetInfo {
  name: string;
  components: string[];
  pins: string[];
  signalType?: string;
}

export default function NetlistView({
  parts,
  connections,
  onNetClick,
}: NetlistViewProps) {
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedNet, setSelectedNet] = useState<string | null>(null);
  const [visibleNets, setVisibleNets] = useState<Set<string>>(
    new Set(connections.map((c) => c.net_name))
  );

  const nets = useMemo(() => {
    const netMap = new Map<string, NetInfo>();

    connections.forEach((conn) => {
      const netName = conn.net_name || "Unnamed";
      if (!netMap.has(netName)) {
        netMap.set(netName, {
          name: netName,
          components: [],
          pins: [],
          signalType: conn.signal_type,
        });
      }

      const net = netMap.get(netName)!;
      if (conn.components) {
        net.components.push(...conn.components);
      }
      if (conn.pins) {
        net.pins.push(...conn.pins);
      }
    });

    return Array.from(netMap.values());
  }, [connections]);

  const filteredNets = useMemo(() => {
    return nets.filter((net) => {
      if (!visibleNets.has(net.name)) return false;
      if (!searchQuery) return true;
      const query = searchQuery.toLowerCase();
      return (
        net.name.toLowerCase().includes(query) ||
        net.components.some((c) => c.toLowerCase().includes(query))
      );
    });
  }, [nets, searchQuery, visibleNets]);

  const toggleNetVisibility = (netName: string) => {
    const newVisible = new Set(visibleNets);
    if (newVisible.has(netName)) {
      newVisible.delete(netName);
    } else {
      newVisible.add(netName);
    }
    setVisibleNets(newVisible);
  };

  const exportNetlist = () => {
    const netlistText = nets
      .map((net) => {
        const components = net.components.join(" ");
        const pins = net.pins.join(" ");
        return `${net.name}: ${components} (${pins})`;
      })
      .join("\n");

    const blob = new Blob([netlistText], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `netlist_${new Date().toISOString().split("T")[0]}.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <Card className="bg-dark-surface border-dark-border p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Network className="w-5 h-5 text-neutral-blue" />
          <h3 className="text-lg font-semibold text-white">Netlist</h3>
          <Badge variant="outline" className="text-xs">
            {nets.length} net(s)
          </Badge>
        </div>
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="outline"
            onClick={exportNetlist}
            className="text-xs"
          >
            <Download className="w-4 h-4 mr-1" />
            Export
          </Button>
        </div>
      </div>

      {/* Search */}
      <div className="mb-4">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-blue" />
          <input
            type="text"
            placeholder="Search nets..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded text-white placeholder-neutral-blue focus:outline-none focus:border-neon-teal"
          />
        </div>
      </div>

      {/* Nets List */}
      <div className="space-y-2 max-h-[600px] overflow-y-auto">
        {filteredNets.map((net) => (
          <div
            key={net.name}
            className={`p-3 rounded border transition-all cursor-pointer ${
              selectedNet === net.name
                ? "bg-neon-teal/10 border-neon-teal"
                : "bg-dark-bg border-dark-border hover:border-zinc-700"
            }`}
            onClick={() => {
              setSelectedNet(net.name);
              onNetClick?.(net.name);
            }}
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-white font-mono">
                    {net.name}
                  </span>
                  {net.signalType && (
                    <Badge variant="outline" className="text-xs">
                      {net.signalType}
                    </Badge>
                  )}
                </div>
                <div className="text-xs text-neutral-blue space-y-1">
                  <div>
                    <strong>Components:</strong> {net.components.join(", ")}
                  </div>
                  {net.pins.length > 0 && (
                    <div>
                      <strong>Pins:</strong> {net.pins.join(", ")}
                    </div>
                  )}
                </div>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={(e) => {
                  e.stopPropagation();
                  toggleNetVisibility(net.name);
                }}
                className="h-7 w-7 p-0"
              >
                {visibleNets.has(net.name) ? (
                  <Eye className="w-4 h-4" />
                ) : (
                  <EyeOff className="w-4 h-4" />
                )}
              </Button>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

