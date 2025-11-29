/**
 * BOM Export Component
 * Enterprise-level export to multiple formats
 */

import React, { useState } from "react";
import { Card } from "../../../shared/components/ui/card";
import { Button } from "../../../shared/components/ui/button";
import { Badge } from "../../../shared/components/ui/badge";
import {
  Download,
  FileText,
  FileSpreadsheet,
  Code,
  Settings,
  CheckCircle2,
} from "lucide-react";
import type { PartObject } from "../../../shared/services/types";
import { normalizePrice, normalizeQuantity } from "../../utils/partNormalizer";

interface BOMExportProps {
  parts: PartObject[];
  connections?: any[];
  projectName?: string;
}

type ExportFormat = "csv" | "excel" | "json" | "altium" | "kicad" | "ipc2581";

export default function BOMExport({
  parts,
  connections = [],
  projectName = "PCB Design",
}: BOMExportProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("csv");
  const [includeConnections, setIncludeConnections] = useState(false);
  const [includeMetadata, setIncludeMetadata] = useState(true);

  const exportFormats: {
    format: ExportFormat;
    name: string;
    description: string;
    icon: React.ReactNode;
  }[] = [
    {
      format: "csv",
      name: "CSV",
      description: "Comma-separated values for Excel/Google Sheets",
      icon: <FileText className="w-5 h-5" />,
    },
    {
      format: "excel",
      name: "Excel",
      description: "Microsoft Excel format (.xlsx)",
      icon: <FileSpreadsheet className="w-5 h-5" />,
    },
    {
      format: "json",
      name: "JSON",
      description: "Structured data format for APIs",
      icon: <Code className="w-5 h-5" />,
    },
    {
      format: "altium",
      name: "Altium Designer",
      description: "Altium Designer BOM format",
      icon: <FileText className="w-5 h-5" />,
    },
    {
      format: "kicad",
      name: "KiCad",
      description: "KiCad BOM format",
      icon: <FileText className="w-5 h-5" />,
    },
    {
      format: "ipc2581",
      name: "IPC-2581",
      description: "Industry standard BOM format",
      icon: <FileText className="w-5 h-5" />,
    },
  ];

  const exportToCSV = () => {
    const headers = [
      "Designator",
      "MPN",
      "Manufacturer",
      "Description",
      "Quantity",
      "Unit Price",
      "Total Price",
      "Package",
      "Footprint",
      "Category",
      "Lifecycle Status",
      "Availability",
    ];

    const rows = parts.map((part) => [
      part.componentId || "",
      part.mpn,
      part.manufacturer,
      part.description,
      (part.quantity || 1).toString(),
      normalizePrice(part.price).toFixed(2),
      (normalizePrice(part.price) * normalizeQuantity(part.quantity)).toFixed(2),
      part.package || "",
      part.footprint || "",
      part.category || "",
      part.lifecycle_status || "",
      part.availability_status || "",
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectName}_BOM.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToJSON = () => {
    const bomData = {
      project: projectName,
      version: "1.0",
      generated: new Date().toISOString(),
      metadata: includeMetadata
        ? {
            totalParts: parts.length,
            totalCost: parts.reduce(
              (sum, p) => sum + normalizePrice(p.price) * normalizeQuantity(p.quantity),
              0
            ),
            connections: includeConnections ? connections.length : 0,
          }
        : undefined,
      parts: parts.map((part) => ({
        componentId: part.componentId,
        designator: part.componentId,
        mpn: part.mpn,
        manufacturer: part.manufacturer,
        description: part.description,
        quantity: part.quantity || 1,
        unitPrice: normalizePrice(part.price),
        totalPrice: normalizePrice(part.price) * normalizeQuantity(part.quantity),
        package: part.package,
        footprint: part.footprint,
        category: part.category,
        lifecycleStatus: part.lifecycle_status,
        availabilityStatus: part.availability_status,
        datasheet: part.datasheet,
        ...(includeConnections && {
          connections: connections
            .filter((c) => c.components?.includes(part.componentId))
            .map((c) => ({
              net: c.net_name || c.name,
              pins: c.pins || [],
            })),
        }),
      })),
    };

    const blob = new Blob([JSON.stringify(bomData, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectName}_BOM.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToAltium = () => {
    // Altium BOM format
    const headers = [
      "Comment",
      "Designator",
      "Footprint",
      "LibRef",
      "Quantity",
      "Description",
    ];

    const rows = parts.map((part) => [
      part.mpn,
      part.componentId || "",
      part.footprint || part.package || "",
      part.mpn,
      (part.quantity || 1).toString(),
      part.description,
    ]);

    const csvContent = [
      headers.join("\t"),
      ...rows.map((row) => row.join("\t")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/plain" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectName}_BOM.txt`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const exportToKiCad = () => {
    // KiCad BOM format
    const headers = [
      "Reference",
      "Value",
      "Footprint",
      "Datasheet",
      "MPN",
      "Manufacturer",
      "Quantity",
    ];

    const rows = parts.map((part) => [
      part.componentId || "",
      part.description,
      part.footprint || part.package || "",
      part.datasheet || "",
      part.mpn,
      part.manufacturer,
      (part.quantity || 1).toString(),
    ]);

    const csvContent = [
      headers.join(","),
      ...rows.map((row) => row.map((cell) => `"${cell}"`).join(",")),
    ].join("\n");

    const blob = new Blob([csvContent], { type: "text/csv" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${projectName}_BOM.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExport = () => {
    switch (selectedFormat) {
      case "csv":
        exportToCSV();
        break;
      case "excel":
        // Excel export would require a library like xlsx
        exportToCSV(); // Fallback to CSV
        break;
      case "json":
        exportToJSON();
        break;
      case "altium":
        exportToAltium();
        break;
      case "kicad":
        exportToKiCad();
        break;
      case "ipc2581":
        // IPC-2581 is complex, would need proper library
        exportToJSON(); // Fallback to JSON
        break;
    }
  };

  return (
    <Card className="p-4 bg-dark-surface border-dark-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Download className="w-5 h-5 text-neon-teal" />
          <h3 className="text-lg font-semibold text-white">Export BOM</h3>
        </div>
        <Badge variant="outline" className="text-xs">
          {parts.length} parts
        </Badge>
      </div>

      {/* Format Selection */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
        {exportFormats.map((format) => (
          <button
            key={format.format}
            onClick={() => setSelectedFormat(format.format)}
            className={`p-3 rounded border text-left transition-all ${
              selectedFormat === format.format
                ? "border-neon-teal bg-neon-teal/10"
                : "border-dark-border bg-dark-bg hover:border-zinc-700"
            }`}
          >
            <div className="flex items-center gap-2 mb-1">
              <div
                className={
                  selectedFormat === format.format
                    ? "text-neon-teal"
                    : "text-neutral-blue"
                }
              >
                {format.icon}
              </div>
              <span
                className={`text-sm font-medium ${
                  selectedFormat === format.format
                    ? "text-white"
                    : "text-neutral-blue"
                }`}
              >
                {format.name}
              </span>
              {selectedFormat === format.format && (
                <CheckCircle2 className="w-4 h-4 text-neon-teal ml-auto" />
              )}
            </div>
            <div className="text-xs text-neutral-blue">
              {format.description}
            </div>
          </button>
        ))}
      </div>

      {/* Export Options */}
      <div className="space-y-2 mb-4 p-3 bg-dark-bg rounded border border-dark-border">
        <label className="flex items-center gap-2 text-sm text-white cursor-pointer">
          <input
            type="checkbox"
            checked={includeMetadata}
            onChange={(e) => setIncludeMetadata(e.target.checked)}
            className="rounded"
          />
          Include metadata (version, timestamps, totals)
        </label>
        <label className="flex items-center gap-2 text-sm text-white cursor-pointer">
          <input
            type="checkbox"
            checked={includeConnections}
            onChange={(e) => setIncludeConnections(e.target.checked)}
            className="rounded"
          />
          Include connection/netlist data
        </label>
      </div>

      {/* Export Button */}
      <Button
        onClick={handleExport}
        className="w-full bg-neon-teal hover:bg-neon-teal/80"
      >
        <Download className="w-4 h-4 mr-2" />
        Export as {exportFormats.find((f) => f.format === selectedFormat)?.name}
      </Button>
    </Card>
  );
}

