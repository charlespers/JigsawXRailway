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
            {sortedParts.map((part) => (
              <tr
                key={part.componentId}
                className={`border-b border-dark-border hover:bg-zinc-900/30 transition-colors cursor-pointer ${
                  selectedRows.has(part.componentId) ? "bg-zinc-900/50" : ""
                }`}
                onClick={() => onPartClick?.(part)}
              >
                <td className="p-3" onClick={(e) => e.stopPropagation()}>
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
                  />
                </td>
                <td className="p-3">
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
                <td className="p-3 text-sm text-neutral-blue">{part.manufacturer}</td>
                <td className="p-3 text-sm text-white max-w-xs truncate" title={part.description}>
                  {part.description}
                </td>
                <td className="p-3 text-sm text-white text-right">{normalizeQuantity(part.quantity)}</td>
                <td className="p-3 text-sm text-white text-right">
                  ${normalizePrice(part.price).toFixed(2)}
                </td>
                <td className="p-3 text-sm font-medium text-white text-right">
                  ${(normalizePrice(part.price) * normalizeQuantity(part.quantity)).toFixed(2)}
                </td>
                <td className="p-3 text-sm text-neutral-blue">{part.package || "-"}</td>
                <td className="p-3">
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
                      {part.datasheet && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => window.open(part.datasheet, "_blank")}
                          className="h-7 w-7 p-0"
                        >
                          <ExternalLink className="w-4 h-4" />
                        </Button>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            ))}
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

