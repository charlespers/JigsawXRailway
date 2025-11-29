/**
 * Professional BOM Table Component
 * Advanced table with virtualization, sorting, filtering
 */

import React, { useMemo, useState } from "react";
import { Card } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import {
  ArrowUpDown,
  ArrowUp,
  ArrowDown,
  Filter,
  Download,
  Copy,
  ExternalLink,
  ChevronDown,
  ChevronRight,
  Zap,
  Cpu,
  FileText,
} from "lucide-react";
import type { PartObject } from "../../services/types";
import { normalizePrice, normalizeQuantity } from "../../utils/partNormalizer";

interface BOMTableProps {
  parts: PartObject[];
  onPartClick?: (part: PartObject) => void;
  showActions?: boolean;
}

type SortField = keyof PartObject;
type SortDirection = "asc" | "desc";

export default function BOMTable({ 
  parts, 
  onPartClick,
  showActions = true 
}: BOMTableProps) {
  const [sortField, setSortField] = useState<SortField>("mpn");
  const [sortDirection, setSortDirection] = useState<SortDirection>("asc");
  const [selectedRows, setSelectedRows] = useState<Set<string>>(new Set());
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  const sortedParts = useMemo(() => {
    const sorted = [...parts].sort((a, b) => {
      const aVal = a[sortField];
      const bVal = b[sortField];
      
      if (aVal === undefined && bVal === undefined) return 0;
      if (aVal === undefined) return 1;
      if (bVal === undefined) return -1;
      
      let comparison = 0;
      if (typeof aVal === "string" && typeof bVal === "string") {
        comparison = aVal.localeCompare(bVal);
      } else if (typeof aVal === "number" && typeof bVal === "number") {
        comparison = aVal - bVal;
      } else {
        comparison = String(aVal).localeCompare(String(bVal));
      }
      
      return sortDirection === "asc" ? comparison : -comparison;
    });
    
    return sorted;
  }, [parts, sortField, sortDirection]);

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === "asc" ? "desc" : "asc");
    } else {
      setSortField(field);
      setSortDirection("asc");
    }
  };

  const SortIcon = ({ field }: { field: SortField }) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-3 h-3 ml-1" />;
    }
    return sortDirection === "asc" ? (
      <ArrowUp className="w-3 h-3 ml-1" />
    ) : (
      <ArrowDown className="w-3 h-3 ml-1" />
    );
  };

  const totalCost = useMemo(() => {
    return sortedParts.reduce(
      (sum, part) => sum + normalizePrice(part.price) * normalizeQuantity(part.quantity),
      0
    );
  }, [sortedParts]);

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
  };

  return (
    <Card className="bg-dark-surface border-dark-border overflow-hidden">
      <div className="overflow-x-auto">
        <table className="w-full border-collapse">
          <thead className="bg-zinc-900/50 border-b border-dark-border">
            <tr>
              <th className="p-3 text-left text-xs font-medium text-neutral-blue">
                <input
                  type="checkbox"
                  checked={selectedRows.size === sortedParts.length && sortedParts.length > 0}
                  onChange={(e) => {
                    if (e.target.checked) {
                      setSelectedRows(new Set(sortedParts.map(p => p.componentId)));
                    } else {
                      setSelectedRows(new Set());
                    }
                  }}
                  className="rounded"
                />
              </th>
              <th className="p-3 text-left">
                <button
                  onClick={() => handleSort("mpn")}
                  className="flex items-center text-xs font-medium text-neutral-blue hover:text-white transition-colors"
                >
                  MPN
                  <SortIcon field="mpn" />
                </button>
              </th>
              <th className="p-3 text-left">
                <button
                  onClick={() => handleSort("manufacturer")}
                  className="flex items-center text-xs font-medium text-neutral-blue hover:text-white transition-colors"
                >
                  Manufacturer
                  <SortIcon field="manufacturer" />
                </button>
              </th>
              <th className="p-3 text-left">
                <button
                  onClick={() => handleSort("description")}
                  className="flex items-center text-xs font-medium text-neutral-blue hover:text-white transition-colors"
                >
                  Description
                  <SortIcon field="description" />
                </button>
              </th>
              <th className="p-3 text-right">
                <button
                  onClick={() => handleSort("quantity")}
                  className="flex items-center ml-auto text-xs font-medium text-neutral-blue hover:text-white transition-colors"
                >
                  Qty
                  <SortIcon field="quantity" />
                </button>
              </th>
              <th className="p-3 text-right">
                <button
                  onClick={() => handleSort("price")}
                  className="flex items-center ml-auto text-xs font-medium text-neutral-blue hover:text-white transition-colors"
                >
                  Unit Price
                  <SortIcon field="price" />
                </button>
              </th>
              <th className="p-3 text-right text-xs font-medium text-neutral-blue">
                Total
              </th>
              <th className="p-3 text-left text-xs font-medium text-neutral-blue">
                Package
              </th>
              <th className="p-3 text-left text-xs font-medium text-neutral-blue">
                Status
              </th>
              {showActions && (
                <th className="p-3 text-center text-xs font-medium text-neutral-blue">
                  Actions
                </th>
              )}
            </tr>
          </thead>
          <tbody>
            {sortedParts.map((part) => {
              const isExpanded = expandedRows.has(part.componentId);
              const partData = (part as any).partData || part;
              const voltage = partData.voltage || part.voltage;
              const pinout = partData.pinout || (part as any).pinout;
              const interfaces = partData.interfaces || part.interfaces || [];
              const footprint = partData.footprint || part.footprint;
              const datasheetUrl = partData.datasheet_url || part.datasheet || partData.datasheet;
              
              return (
                <React.Fragment key={part.componentId}>
                  <tr
                    className={`border-b border-dark-border hover:bg-zinc-900/30 transition-colors ${
                      selectedRows.has(part.componentId) ? "bg-zinc-900/50" : ""
                    }`}
                  >
                    <td className="p-3">
                      <div className="flex items-center gap-2">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            const newExpanded = new Set(expandedRows);
                            if (isExpanded) {
                              newExpanded.delete(part.componentId);
                            } else {
                              newExpanded.add(part.componentId);
                            }
                            setExpandedRows(newExpanded);
                          }}
                          className="text-neutral-blue hover:text-white"
                        >
                          {isExpanded ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
                        <input
                          type="checkbox"
                          checked={selectedRows.has(part.componentId)}
                          onChange={(e) => {
                            const newSelected = new Set(selectedRows);
                            if (e.target.checked) {
                              newSelected.add(part.componentId);
                            } else {
                              newSelected.delete(part.componentId);
                            }
                            setSelectedRows(newSelected);
                          }}
                          className="rounded"
                          onClick={(e) => e.stopPropagation()}
                        />
                      </div>
                    </td>
                    <td className="p-3" onClick={() => onPartClick?.(part)}>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white font-mono">{part.mpn}</span>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            copyToClipboard(part.mpn);
                          }}
                          className="opacity-0 group-hover:opacity-100 hover:text-neon-teal transition-opacity"
                        >
                          <Copy className="w-3 h-3" />
                        </button>
                      </div>
                    </td>
                    <td className="p-3 text-sm text-neutral-blue" onClick={() => onPartClick?.(part)}>
                      {part.manufacturer}
                    </td>
                    <td className="p-3 text-sm text-white max-w-xs truncate" title={part.description} onClick={() => onPartClick?.(part)}>
                      {part.description}
                    </td>
                    <td className="p-3 text-sm text-white text-right" onClick={() => onPartClick?.(part)}>
                      {normalizeQuantity(part.quantity)}
                    </td>
                    <td className="p-3 text-sm text-white text-right" onClick={() => onPartClick?.(part)}>
                      ${normalizePrice(part.price).toFixed(2)}
                    </td>
                    <td className="p-3 text-sm font-medium text-white text-right" onClick={() => onPartClick?.(part)}>
                      ${(normalizePrice(part.price) * normalizeQuantity(part.quantity)).toFixed(2)}
                    </td>
                    <td className="p-3 text-sm text-neutral-blue" onClick={() => onPartClick?.(part)}>
                      {part.package || "-"}
                    </td>
                    <td className="p-3" onClick={() => onPartClick?.(part)}>
                      <div className="flex items-center gap-2">
                        {part.lifecycle_status && (
                          <Badge
                            variant={
                              part.lifecycle_status === "active" ? "default" : "destructive"
                            }
                            className="text-xs"
                          >
                            {part.lifecycle_status}
                          </Badge>
                        )}
                        {part.availability_status && (
                          <Badge
                            variant={
                              part.availability_status === "in_stock" ? "default" : "destructive"
                            }
                            className="text-xs"
                          >
                            {part.availability_status}
                          </Badge>
                        )}
                      </div>
                    </td>
                    {showActions && (
                      <td className="p-3" onClick={(e) => e.stopPropagation()}>
                        <div className="flex items-center justify-center gap-1">
                          {datasheetUrl && (
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => window.open(datasheetUrl, "_blank")}
                              className="h-7 w-7 p-0"
                              title="View Datasheet"
                            >
                              <ExternalLink className="w-4 h-4" />
                            </Button>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                  {isExpanded && (
                    <tr className="bg-zinc-900/30 border-b border-dark-border">
                      <td colSpan={showActions ? 10 : 9} className="p-4">
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                          {/* Voltage */}
                          {voltage && (
                            <div className="flex items-start gap-2">
                              <Zap className="w-4 h-4 text-yellow-400 mt-0.5" />
                              <div>
                                <div className="text-xs text-neutral-blue">Voltage</div>
                                <div className="text-sm text-white">{voltage}</div>
                              </div>
                            </div>
                          )}
                          
                          {/* Footprint */}
                          {footprint && (
                            <div className="flex items-start gap-2">
                              <Cpu className="w-4 h-4 text-blue-400 mt-0.5" />
                              <div>
                                <div className="text-xs text-neutral-blue">Footprint</div>
                                <div className="text-sm text-white font-mono">{footprint}</div>
                              </div>
                            </div>
                          )}
                          
                          {/* Interfaces */}
                          {interfaces && interfaces.length > 0 && (
                            <div className="flex items-start gap-2">
                              <Cpu className="w-4 h-4 text-green-400 mt-0.5" />
                              <div>
                                <div className="text-xs text-neutral-blue">Interfaces</div>
                                <div className="flex flex-wrap gap-1 mt-1">
                                  {(Array.isArray(interfaces) ? interfaces : [interfaces]).map((iface: string, idx: number) => (
                                    <Badge key={idx} variant="outline" className="text-xs">
                                      {iface}
                                    </Badge>
                                  ))}
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Pinout */}
                          {pinout && typeof pinout === "object" && Object.keys(pinout).length > 0 && (
                            <div className="md:col-span-2 lg:col-span-3">
                              <div className="flex items-start gap-2">
                                <Cpu className="w-4 h-4 text-purple-400 mt-0.5" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-2">Pinout</div>
                                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                                    {Object.entries(pinout).slice(0, 12).map(([pin, desc]: [string, any]) => (
                                      <div key={pin} className="text-xs bg-zinc-800/50 p-2 rounded">
                                        <span className="text-neon-teal font-mono">{pin}:</span>{" "}
                                        <span className="text-white">{typeof desc === "string" ? desc : JSON.stringify(desc)}</span>
                                      </div>
                                    ))}
                                  </div>
                                  {Object.keys(pinout).length > 12 && (
                                    <div className="text-xs text-neutral-blue mt-2">
                                      +{Object.keys(pinout).length - 12} more pins
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Documentation */}
                          {datasheetUrl && (
                            <div className="flex items-start gap-2">
                              <FileText className="w-4 h-4 text-blue-400 mt-0.5" />
                              <div>
                                <div className="text-xs text-neutral-blue">Documentation</div>
                                <a
                                  href={datasheetUrl}
                                  target="_blank"
                                  rel="noopener noreferrer"
                                  className="text-sm text-blue-400 hover:text-blue-300 underline"
                                >
                                  View Datasheet
                                </a>
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    )}
                  </tr>
                </React.Fragment>
              );
            })}
          </tbody>
          <tfoot className="bg-zinc-900/50 border-t border-dark-border">
            <tr>
              <td colSpan={6} className="p-3 text-sm font-medium text-white text-right">
                Total:
              </td>
              <td className="p-3 text-sm font-bold text-white text-right">
                ${totalCost.toFixed(2)}
              </td>
              <td colSpan={showActions ? 3 : 2}></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </Card>
  );
}

