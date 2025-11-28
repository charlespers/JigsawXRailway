/**
 * Export Dialog Component
 * Professional export interface for multiple formats
 */

import React, { useState } from "react";
import { Card } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import {
  Download,
  FileText,
  FileSpreadsheet,
  FileCode,
  X,
  Check,
} from "lucide-react";
import type { PartObject } from "../../services/types";
import apiClient from "../../services/apiClient";

interface ExportDialogProps {
  parts: PartObject[];
  connections?: any[];
  onClose: () => void;
}

type ExportFormat = "excel" | "csv" | "json" | "pdf" | "altium" | "kicad";

interface FormatOption {
  id: ExportFormat;
  name: string;
  description: string;
  icon: React.ReactNode;
  extension: string;
}

const exportFormats: FormatOption[] = [
  {
    id: "excel",
    name: "Excel (XLSX)",
    description: "Microsoft Excel format with formatting",
    icon: <FileSpreadsheet className="w-5 h-5" />,
    extension: ".xlsx",
  },
  {
    id: "csv",
    name: "CSV",
    description: "Comma-separated values",
    icon: <FileSpreadsheet className="w-5 h-5" />,
    extension: ".csv",
  },
  {
    id: "json",
    name: "JSON",
    description: "Complete design data in JSON format",
    icon: <FileCode className="w-5 h-5" />,
    extension: ".json",
  },
  {
    id: "pdf",
    name: "PDF Report",
    description: "Formatted PDF report with BOM and analysis",
    icon: <FileText className="w-5 h-5" />,
    extension: ".pdf",
  },
  {
    id: "altium",
    name: "Altium Designer",
    description: "Altium Designer netlist and BOM",
    icon: <FileCode className="w-5 h-5" />,
    extension: ".txt",
  },
  {
    id: "kicad",
    name: "KiCad",
    description: "KiCad netlist and BOM",
    icon: <FileCode className="w-5 h-5" />,
    extension: ".net",
  },
];

export default function ExportDialog({
  parts,
  connections = [],
  onClose,
}: ExportDialogProps) {
  const [selectedFormat, setSelectedFormat] = useState<ExportFormat>("excel");
  const [exporting, setExporting] = useState(false);
  const [exported, setExported] = useState(false);

  const handleExport = async () => {
    if (parts.length === 0) {
      return;
    }

    setExporting(true);

    try {
      const bomItems = parts.map(part => ({
        part_data: part,
        quantity: part.quantity || 1,
      }));

      if (selectedFormat === "json") {
        // Client-side JSON export
        const designData = {
          parts,
          connections,
          timestamp: new Date().toISOString(),
          version: "1.0",
        };
        const blob = new Blob([JSON.stringify(designData, null, 2)], {
          type: "application/json",
        });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `design_${new Date().toISOString().split("T")[0]}.json`;
        a.click();
        URL.revokeObjectURL(url);
        setExported(true);
      } else {
        // Server-side export
        const response = await apiClient.post("/api/v1/export/download", {
          bom_items: bomItems,
          connections,
          format: selectedFormat,
        });

        // Handle file download
        if (response.file_url) {
          window.open(response.file_url, "_blank");
        } else if (response.file_data) {
          // Base64 encoded file
          const blob = new Blob(
            [Uint8Array.from(atob(response.file_data), (c) => c.charCodeAt(0))],
            { type: "application/octet-stream" }
          );
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = response.filename || `design.${exportFormats.find(f => f.id === selectedFormat)?.extension}`;
          a.click();
          URL.revokeObjectURL(url);
        }
        setExported(true);
      }
    } catch (error: any) {
      console.error("Export failed:", error);
      alert(`Export failed: ${error.message}`);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-2xl bg-dark-surface border-dark-border p-6 max-h-[90vh] overflow-y-auto">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Export Design</h2>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-neutral-blue hover:text-white"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="space-y-4 mb-6">
          <p className="text-sm text-neutral-blue">
            Select a format to export your design. The export will include all
            parts, connections, and design metadata.
          </p>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {exportFormats.map((format) => (
              <button
                key={format.id}
                onClick={() => setSelectedFormat(format.id)}
                className={`p-4 border rounded-lg text-left transition-all ${
                  selectedFormat === format.id
                    ? "border-neon-teal bg-neon-teal/10"
                    : "border-dark-border hover:border-zinc-700"
                }`}
              >
                <div className="flex items-start gap-3">
                  <div
                    className={`${
                      selectedFormat === format.id
                        ? "text-neon-teal"
                        : "text-neutral-blue"
                    }`}
                  >
                    {format.icon}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <h3 className="text-sm font-medium text-white">
                        {format.name}
                      </h3>
                      {selectedFormat === format.id && (
                        <Check className="w-4 h-4 text-neon-teal" />
                      )}
                    </div>
                    <p className="text-xs text-neutral-blue">
                      {format.description}
                    </p>
                  </div>
                </div>
              </button>
            ))}
          </div>
        </div>

        <div className="flex items-center justify-between pt-4 border-t border-dark-border">
          <div className="text-sm text-neutral-blue">
            {parts.length} part(s) • {connections.length} connection(s)
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={handleExport}
              disabled={exporting || exported || parts.length === 0}
              className="bg-neon-teal hover:bg-neon-teal/80 text-dark-bg"
            >
              {exporting ? (
                "Exporting..."
              ) : exported ? (
                <>
                  <Check className="w-4 h-4 mr-2" />
                  Exported
                </>
              ) : (
                <>
                  <Download className="w-4 h-4 mr-2" />
                  Export
                </>
              )}
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

