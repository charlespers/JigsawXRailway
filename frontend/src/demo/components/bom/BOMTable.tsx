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
  Thermometer,
  Clock,
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
  const [categoryFilter, setCategoryFilter] = useState<string>("all");
  const [showFilters, setShowFilters] = useState(false);

  // Filter parts by category
  const filteredParts = useMemo(() => {
    if (categoryFilter === "all") return parts;
    return parts.filter(part => {
      const partCategory = part.category?.toLowerCase() || "";
      return partCategory.includes(categoryFilter.toLowerCase());
    });
  }, [parts, categoryFilter]);

  const sortedParts = useMemo(() => {
    const sorted = [...filteredParts].sort((a, b) => {
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
  }, [filteredParts, sortField, sortDirection]);

  // Calculate power consumption for a part
  const calculatePowerConsumption = (part: PartObject): number => {
    const partData = (part as any).partData || part;
    const currentMax = partData.current_max || {};
    const supplyVoltageRange = partData.supply_voltage_range || {};
    const currentMa = currentMax.output || currentMax.input || 0;
    const voltage = supplyVoltageRange.nominal || supplyVoltageRange.max || 3.3;
    if (currentMa > 0) {
      return (currentMa / 1000.0) * voltage * 1000; // Convert to mW
    }
    return 0;
  };

  // Get temperature rating
  const getTemperatureRating = (part: PartObject): string | null => {
    const partData = (part as any).partData || part;
    const tempRange = partData.operating_temp_range || {};
    if (tempRange.min !== undefined && tempRange.max !== undefined) {
      return `${tempRange.min}°C to ${tempRange.max}°C`;
    }
    if (part.temperature_rating) {
      return typeof part.temperature_rating === "number" 
        ? `${part.temperature_rating}°C` 
        : String(part.temperature_rating);
    }
    return null;
  };

  // Get lead time
  const getLeadTime = (part: PartObject): string | null => {
    if (part.lead_time_days) {
      if (part.lead_time_days === 0) return "In Stock";
      if (part.lead_time_days < 7) return `${part.lead_time_days} days`;
      if (part.lead_time_days < 30) return `${Math.ceil(part.lead_time_days / 7)} weeks`;
      return `${Math.ceil(part.lead_time_days / 30)} months`;
    }
    return null;
  };

  // Export to CSV
  const exportToCSV = () => {
    const headers = ["MPN", "Manufacturer", "Description", "Qty", "Unit Price", "Total Price", "Package", "Footprint", "Category", "Power (mW)", "Temp Rating", "Lead Time"];
    const rows = sortedParts.map(part => {
      const power = calculatePowerConsumption(part);
      const temp = getTemperatureRating(part);
      const leadTime = getLeadTime(part);
      return [
        part.mpn,
        part.manufacturer,
        part.description,
        normalizeQuantity(part.quantity),
        normalizePrice(part.price).toFixed(2),
        (normalizePrice(part.price) * normalizeQuantity(part.quantity)).toFixed(2),
        part.package || "",
        part.footprint || "",
        part.category || "",
        power > 0 ? power.toFixed(1) : "",
        temp || "",
        leadTime || ""
      ];
    });
    
    const csvContent = [
      headers.join(","),
      ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
    ].join("\n");
    
    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `bom_export_${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  // Get unique categories for filter
  const categories = useMemo(() => {
    const cats = new Set(parts.map(p => p.category).filter(Boolean));
    return Array.from(cats).sort();
  }, [parts]);

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
      {/* Toolbar with filters and export */}
      <div className="p-3 border-b border-dark-border flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Button
            size="sm"
            variant="ghost"
            onClick={() => setShowFilters(!showFilters)}
            className="h-8"
          >
            <Filter className="w-4 h-4 mr-1" />
            Filters
          </Button>
          {showFilters && (
            <select
              value={categoryFilter}
              onChange={(e) => setCategoryFilter(e.target.value)}
              className="h-8 px-2 bg-zinc-800 border border-zinc-700 rounded text-sm text-white"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          )}
          {categoryFilter !== "all" && (
            <Badge variant="outline" className="text-xs">
              {filteredParts.length} of {parts.length} parts
            </Badge>
          )}
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={exportToCSV}
          className="h-8"
        >
          <Download className="w-4 h-4 mr-1" />
          Export CSV
        </Button>
      </div>
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
              <th className="p-3 text-right text-xs font-medium text-neutral-blue">
                Power
              </th>
              <th className="p-3 text-left text-xs font-medium text-neutral-blue">
                Temp Rating
              </th>
              <th className="p-3 text-left text-xs font-medium text-neutral-blue">
                Lead Time
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
              // Extract partData with comprehensive fallbacks
              const partData = (part as any).partData || part;
              
              // Extract voltage with multiple fallback strategies
              let voltage = partData.voltage || part.voltage;
              if (!voltage && partData.supply_voltage_range) {
                const range = partData.supply_voltage_range;
                if (range.nominal) {
                  voltage = `${range.nominal}V`;
                } else if (range.min && range.max) {
                  voltage = `${range.min}-${range.max}V`;
                }
              }
              
              // Extract all specs with fallbacks
              const pinout = partData.pinout || (part as any).pinout || {};
              const interfaces = partData.interface_type || partData.interfaces || part.interfaces || [];
              const footprint = partData.footprint || part.footprint || partData.package || part.package;
              const datasheetUrl = partData.datasheet_url || part.datasheet || partData.datasheet;
              const supplyVoltageRange = partData.supply_voltage_range || {};
              const operatingTempRange = partData.operating_temp_range || {};
              const currentMax = partData.current_max || {};
              const description = partData.description || part.description || '';
              const manufacturer = partData.manufacturer || part.manufacturer || '';
              
              // Format temperature range
              let tempRange = null;
              if (operatingTempRange.min !== undefined && operatingTempRange.max !== undefined) {
                tempRange = `${operatingTempRange.min}°C to ${operatingTempRange.max}°C`;
              }
              
              // Format current rating
              let currentRating = null;
              if (currentMax.output !== undefined) {
                const unit = currentMax.unit || 'A';
                currentRating = `${currentMax.output}${unit}`;
              }
              
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
                    <td className="p-3 text-sm text-right text-neutral-blue" onClick={() => onPartClick?.(part)}>
                      {(() => {
                        const power = calculatePowerConsumption(part);
                        return power > 0 ? `${power.toFixed(1)}mW` : "-";
                      })()}
                    </td>
                    <td className="p-3 text-sm text-neutral-blue" onClick={() => onPartClick?.(part)}>
                      {getTemperatureRating(part) || "-"}
                    </td>
                    <td className="p-3 text-sm text-neutral-blue" onClick={() => onPartClick?.(part)}>
                      {getLeadTime(part) || "-"}
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
                      <td colSpan={showActions ? 13 : 12} className="p-4">
                        <div className="space-y-4">
                          {/* Basic Information Grid */}
                          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                            {/* Voltage */}
                            {voltage && (
                              <div className="flex items-start gap-2">
                                <Zap className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-1">Supply Voltage</div>
                                  <div className="text-sm text-white font-medium">{voltage}</div>
                                  {supplyVoltageRange.min && supplyVoltageRange.max && (
                                    <div className="text-xs text-neutral-blue mt-1">
                                      Range: {supplyVoltageRange.min}V - {supplyVoltageRange.max}V
                                    </div>
                                  )}
                                </div>
                              </div>
                            )}
                            
                            {/* Temperature Range */}
                            {tempRange && (
                              <div className="flex items-start gap-2">
                                <Cpu className="w-4 h-4 text-orange-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-1">Operating Temperature</div>
                                  <div className="text-sm text-white font-medium">{tempRange}</div>
                                </div>
                              </div>
                            )}
                            
                            {/* Current Rating */}
                            {currentRating && (
                              <div className="flex items-start gap-2">
                                <Zap className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-1">Max Current</div>
                                  <div className="text-sm text-white font-medium">{currentRating}</div>
                                </div>
                              </div>
                            )}
                            
                            {/* Footprint */}
                            {footprint && (
                              <div className="flex items-start gap-2">
                                <Cpu className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-1">Footprint (IPC-7351)</div>
                                  <div className="text-sm text-white font-mono">{footprint}</div>
                                </div>
                              </div>
                            )}
                            
                            {/* Package */}
                            {part.package && part.package !== footprint && (
                              <div className="flex items-start gap-2">
                                <Cpu className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-1">Package</div>
                                  <div className="text-sm text-white font-medium">{part.package}</div>
                                </div>
                              </div>
                            )}
                            
                            {/* Documentation */}
                            {datasheetUrl && (
                              <div className="flex items-start gap-2">
                                <FileText className="w-4 h-4 text-blue-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-1">Documentation</div>
                                  <a
                                    href={datasheetUrl}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="text-sm text-blue-400 hover:text-blue-300 underline inline-flex items-center gap-1"
                                  >
                                    View Datasheet
                                    <ExternalLink className="w-3 h-3" />
                                  </a>
                                </div>
                              </div>
                            )}
                          </div>
                          
                          {/* Interfaces */}
                          {interfaces && interfaces.length > 0 && (
                            <div className="border-t border-zinc-700 pt-4">
                              <div className="flex items-start gap-2">
                                <Cpu className="w-4 h-4 text-green-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-2">Supported Interfaces</div>
                                  <div className="flex flex-wrap gap-2">
                                    {(Array.isArray(interfaces) ? interfaces : [interfaces]).map((iface: string, idx: number) => (
                                      <Badge key={idx} variant="outline" className="text-xs border-green-500/50 text-green-400">
                                        {iface}
                                      </Badge>
                                    ))}
                                  </div>
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Pinout */}
                          {pinout && typeof pinout === "object" && Object.keys(pinout).length > 0 && (
                            <div className="border-t border-zinc-700 pt-4">
                              <div className="flex items-start gap-2">
                                <Cpu className="w-4 h-4 text-purple-400 mt-0.5 flex-shrink-0" />
                                <div className="flex-1">
                                  <div className="text-xs text-neutral-blue mb-2">Pinout</div>
                                  <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2">
                                    {Object.entries(pinout).slice(0, 16).map(([pin, desc]: [string, any]) => (
                                      <div key={pin} className="text-xs bg-zinc-800/50 p-2 rounded border border-zinc-700">
                                        <span className="text-neon-teal font-mono font-semibold">{pin}:</span>{" "}
                                        <span className="text-white">{typeof desc === "string" ? desc : JSON.stringify(desc)}</span>
                                      </div>
                                    ))}
                                  </div>
                                  {Object.keys(pinout).length > 16 && (
                                    <div className="text-xs text-neutral-blue mt-2">
                                      +{Object.keys(pinout).length - 16} more pins (see datasheet for complete pinout)
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          )}
                          
                          {/* Full Description */}
                          {description && description.length > 50 && (
                            <div className="border-t border-zinc-700 pt-4">
                              <div className="text-xs text-neutral-blue mb-1">Full Description</div>
                              <div className="text-sm text-white">{description}</div>
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
              <td colSpan={showActions ? 6 : 5}></td>
            </tr>
          </tfoot>
        </table>
      </div>
    </Card>
  );
}

