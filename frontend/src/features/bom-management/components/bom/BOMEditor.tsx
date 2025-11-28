/**
 * Advanced BOM Editor Component
 * Professional BOM editing interface for electrical engineers
 */

import React, { useState, useMemo } from "react";
import { Card } from "../../shared/components/ui/card";
import { Button } from "../../shared/components/ui/button";
import { Badge } from "../../shared/components/ui/badge";
import {
  Edit2,
  Trash2,
  Plus,
  Save,
  X,
  Search,
  Filter,
  Download,
  Copy,
  Check,
  AlertCircle,
} from "lucide-react";
import type { PartObject } from "../../shared/services/types";
import { useBOMManagement } from "../../hooks/useBOMManagement";
import { normalizePrice, normalizeQuantity } from "../../utils/partNormalizer";

interface BOMEditorProps {
  parts: PartObject[];
  onPartsChange?: (parts: PartObject[]) => void;
}

type SortField = "mpn" | "manufacturer" | "price" | "quantity" | "category";
type GroupBy = "none" | "category" | "manufacturer" | "package";

export default function BOMEditor({ parts, onPartsChange }: BOMEditorProps) {
  const { updatePartInBOM, removePartFromBOM, bulkUpdateParts } = useBOMManagement();
  
  const [searchQuery, setSearchQuery] = useState("");
  const [sortField, setSortField] = useState<SortField>("mpn");
  const [sortDirection, setSortDirection] = useState<"asc" | "desc">("asc");
  const [groupBy, setGroupBy] = useState<GroupBy>("none");
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editData, setEditData] = useState<Partial<PartObject>>({});
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());

  // Filter and sort parts
  const filteredAndSortedParts = useMemo(() => {
    let filtered = parts.filter(part => {
      const query = searchQuery.toLowerCase();
      return (
        part.mpn.toLowerCase().includes(query) ||
        part.manufacturer.toLowerCase().includes(query) ||
        part.description.toLowerCase().includes(query) ||
        part.category?.toLowerCase().includes(query) ||
        ""
      );
    });

    // Sort
    filtered.sort((a, b) => {
      let aVal: any = a[sortField];
      let bVal: any = b[sortField];
      
      if (sortField === "price") {
        aVal = a.price || 0;
        bVal = b.price || 0;
      }
      
      if (typeof aVal === "string") {
        aVal = aVal.toLowerCase();
        bVal = bVal.toLowerCase();
      }
      
      const comparison = aVal < bVal ? -1 : aVal > bVal ? 1 : 0;
      return sortDirection === "asc" ? comparison : -comparison;
    });

    return filtered;
  }, [parts, searchQuery, sortField, sortDirection]);

  // Group parts
  const groupedParts = useMemo(() => {
    if (groupBy === "none") {
      return { "All Parts": filteredAndSortedParts };
    }

    const groups: Record<string, PartObject[]> = {};
    filteredAndSortedParts.forEach(part => {
      const key = part[groupBy] || "Unknown";
      if (!groups[key]) {
        groups[key] = [];
      }
      groups[key].push(part);
    });

    return groups;
  }, [filteredAndSortedParts, groupBy]);

  const startEdit = (part: PartObject) => {
    setEditingId(part.componentId);
    setEditData({
      quantity: part.quantity,
      price: part.price,
      description: part.description,
      assembly_notes: part.assembly_notes,
    });
  };

  const saveEdit = () => {
    if (editingId) {
      updatePartInBOM(editingId, editData);
      setEditingId(null);
      setEditData({});
    }
  };

  const cancelEdit = () => {
    setEditingId(null);
    setEditData({});
  };

  const toggleSelection = (componentId: string) => {
    const newSelected = new Set(selectedIds);
    if (newSelected.has(componentId)) {
      newSelected.delete(componentId);
    } else {
      newSelected.add(componentId);
    }
    setSelectedIds(newSelected);
  };

  const deleteSelected = () => {
    selectedIds.forEach(id => removePartFromBOM(id));
    setSelectedIds(new Set());
  };

  const bulkEdit = () => {
    if (selectedIds.size === 0) return;
    
    const updates = Array.from(selectedIds).map(id => ({
      componentId: id,
      updates: editData,
    }));
    
    bulkUpdateParts(updates);
    setSelectedIds(new Set());
    setEditData({});
  };

  return (
    <div className="space-y-4">
      {/* Toolbar */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center justify-between flex-wrap gap-4">
          {/* Search */}
          <div className="flex-1 min-w-[200px]">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-neutral-blue" />
              <input
                type="text"
                placeholder="Search BOM..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="w-full pl-10 pr-4 py-2 bg-dark-bg border border-dark-border rounded text-white placeholder-neutral-blue focus:outline-none focus:border-neon-teal"
              />
            </div>
          </div>

          {/* Sort */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-neutral-blue">Sort:</label>
            <select
              value={sortField}
              onChange={(e) => setSortField(e.target.value as SortField)}
              className="px-3 py-2 bg-dark-bg border border-dark-border rounded text-white text-sm focus:outline-none focus:border-neon-teal"
            >
              <option value="mpn">MPN</option>
              <option value="manufacturer">Manufacturer</option>
              <option value="price">Price</option>
              <option value="quantity">Quantity</option>
              <option value="category">Category</option>
            </select>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setSortDirection(sortDirection === "asc" ? "desc" : "asc")}
              className="text-xs"
            >
              {sortDirection === "asc" ? "↑" : "↓"}
            </Button>
          </div>

          {/* Group By */}
          <div className="flex items-center gap-2">
            <label className="text-sm text-neutral-blue">Group:</label>
            <select
              value={groupBy}
              onChange={(e) => setGroupBy(e.target.value as GroupBy)}
              className="px-3 py-2 bg-dark-bg border border-dark-border rounded text-white text-sm focus:outline-none focus:border-neon-teal"
            >
              <option value="none">None</option>
              <option value="category">Category</option>
              <option value="manufacturer">Manufacturer</option>
              <option value="package">Package</option>
            </select>
          </div>

          {/* Actions */}
          <div className="flex items-center gap-2">
            {selectedIds.size > 0 && (
              <>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={bulkEdit}
                  className="text-xs"
                >
                  <Edit2 className="w-3 h-3 mr-1" />
                  Bulk Edit ({selectedIds.size})
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={deleteSelected}
                  className="text-xs text-red-400 border-red-500/50 hover:bg-red-500/20"
                >
                  <Trash2 className="w-3 h-3 mr-1" />
                  Delete
                </Button>
              </>
            )}
            <Button
              size="sm"
              variant="outline"
              className="text-xs"
            >
              <Download className="w-3 h-3 mr-1" />
              Export
            </Button>
          </div>
        </div>
      </Card>

      {/* BOM Table */}
      <Card className="bg-dark-surface border-dark-border">
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-dark-border">
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">
                  <input
                    type="checkbox"
                    checked={selectedIds.size === filteredAndSortedParts.length && filteredAndSortedParts.length > 0}
                    onChange={(e) => {
                      if (e.target.checked) {
                        setSelectedIds(new Set(filteredAndSortedParts.map(p => p.componentId)));
                      } else {
                        setSelectedIds(new Set());
                      }
                    }}
                    className="rounded"
                  />
                </th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">MPN</th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">Manufacturer</th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">Description</th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">Qty</th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">Price</th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">Total</th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">Package</th>
                <th className="p-3 text-left text-xs font-medium text-neutral-blue">Actions</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(groupedParts).map(([groupName, groupParts]) => (
                <React.Fragment key={groupName}>
                  {groupBy !== "none" && (
                    <tr className="bg-zinc-900/50">
                      <td colSpan={9} className="p-2 px-3 text-sm font-medium text-white">
                        {groupName} ({groupParts.length})
                      </td>
                    </tr>
                  )}
                  {groupParts.map((part) => (
                    <tr
                      key={part.componentId}
                      className={`border-b border-dark-border hover:bg-zinc-900/30 ${
                        selectedIds.has(part.componentId) ? "bg-zinc-900/50" : ""
                      }`}
                    >
                      <td className="p-3">
                        <input
                          type="checkbox"
                          checked={selectedIds.has(part.componentId)}
                          onChange={() => toggleSelection(part.componentId)}
                          className="rounded"
                        />
                      </td>
                      <td className="p-3 text-sm text-white font-mono">{part.mpn}</td>
                      <td className="p-3 text-sm text-neutral-blue">{part.manufacturer}</td>
                      <td className="p-3 text-sm text-white">
                        {editingId === part.componentId ? (
                          <input
                            type="text"
                            value={editData.description || ""}
                            onChange={(e) => setEditData({ ...editData, description: e.target.value })}
                            className="w-full px-2 py-1 bg-dark-bg border border-dark-border rounded text-white text-sm"
                          />
                        ) : (
                          part.description
                        )}
                      </td>
                      <td className="p-3 text-sm text-white">
                        {editingId === part.componentId ? (
                          <input
                            type="number"
                            min="1"
                            value={editData.quantity || 1}
                            onChange={(e) => setEditData({ ...editData, quantity: parseInt(e.target.value) || 1 })}
                            className="w-16 px-2 py-1 bg-dark-bg border border-dark-border rounded text-white text-sm"
                          />
                        ) : (
                          part.quantity || 1
                        )}
                      </td>
                      <td className="p-3 text-sm text-white">
                        {editingId === part.componentId ? (
                          <input
                            type="number"
                            step="0.01"
                            value={editData.price || 0}
                            onChange={(e) => setEditData({ ...editData, price: parseFloat(e.target.value) || 0 })}
                            className="w-20 px-2 py-1 bg-dark-bg border border-dark-border rounded text-white text-sm"
                          />
                        ) : (
                          `$${(part.price || 0).toFixed(2)}`
                        )}
                      </td>
                      <td className="p-3 text-sm text-white font-medium">
                        ${(normalizePrice(part.price) * normalizeQuantity(part.quantity)).toFixed(2)}
                      </td>
                      <td className="p-3 text-sm text-neutral-blue">{part.package || "-"}</td>
                      <td className="p-3">
                        <div className="flex items-center gap-1">
                          {editingId === part.componentId ? (
                            <>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={saveEdit}
                                className="h-7 w-7 p-0 text-green-400 hover:bg-green-500/20"
                              >
                                <Check className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={cancelEdit}
                                className="h-7 w-7 p-0 text-red-400 hover:bg-red-500/20"
                              >
                                <X className="w-4 h-4" />
                              </Button>
                            </>
                          ) : (
                            <>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => startEdit(part)}
                                className="h-7 w-7 p-0 text-neutral-blue hover:bg-zinc-800"
                              >
                                <Edit2 className="w-4 h-4" />
                              </Button>
                              <Button
                                size="sm"
                                variant="ghost"
                                onClick={() => removePartFromBOM(part.componentId)}
                                className="h-7 w-7 p-0 text-red-400 hover:bg-red-500/20"
                              >
                                <Trash2 className="w-4 h-4" />
                              </Button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </React.Fragment>
              ))}
            </tbody>
          </table>
        </div>

        {/* Summary */}
        <div className="p-4 border-t border-dark-border bg-zinc-900/30">
          <div className="flex items-center justify-between">
            <div className="text-sm text-neutral-blue">
              Total: {parts.length} part(s)
            </div>
            <div className="text-sm font-medium text-white">
              Total Cost: ${parts.reduce((sum, p) => sum + (p.price || 0) * (p.quantity || 1), 0).toFixed(2)}
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}

