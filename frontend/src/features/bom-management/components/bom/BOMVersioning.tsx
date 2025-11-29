/**
 * BOM Versioning and Revision Tracking
 * Enterprise-level version control for BOMs
 */

import React, { useState, useMemo } from "react";
import { Card } from "../../../shared/components/ui/card";
import { Button } from "../../../shared/components/ui/button";
import { Badge } from "../../../shared/components/ui/badge";
import {
  GitBranch,
  History,
  Tag,
  Diff,
  Download,
  Clock,
  User,
  MessageSquare,
} from "lucide-react";
import type { PartObject } from "../../../shared/services/types";

interface BOMVersion {
  version: string;
  revision: string;
  timestamp: string;
  author: string;
  description: string;
  parts: PartObject[];
  changes: BOMChange[];
  approved: boolean;
  approvedBy?: string;
  approvedAt?: string;
}

interface BOMChange {
  type: "added" | "removed" | "modified" | "quantity_changed";
  partId: string;
  partMpn: string;
  oldValue?: any;
  newValue?: any;
  field?: string;
}

interface BOMVersioningProps {
  parts: PartObject[];
  currentVersion?: string;
  onVersionCreate?: (version: BOMVersion) => void;
  onVersionRestore?: (version: BOMVersion) => void;
}

export default function BOMVersioning({
  parts,
  currentVersion = "1.0",
  onVersionCreate,
  onVersionRestore,
}: BOMVersioningProps) {
  const [versions, setVersions] = useState<BOMVersion[]>([
    {
      version: "1.0",
      revision: "A",
      timestamp: new Date().toISOString(),
      author: "System",
      description: "Initial BOM",
      parts: parts,
      changes: [],
      approved: true,
      approvedBy: "System",
      approvedAt: new Date().toISOString(),
    },
  ]);
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);
  const [showDiff, setShowDiff] = useState(false);
  const [newVersionDescription, setNewVersionDescription] = useState("");

  const createNewVersion = () => {
    const latestVersion = versions[0];
    const newVersionNumber = parseFloat(latestVersion.version) + 0.1;
    const newRevision = String.fromCharCode(
      latestVersion.revision.charCodeAt(0) + 1
    );

    // Calculate changes
    const changes: BOMChange[] = [];
    const oldPartsMap = new Map(
      latestVersion.parts.map((p) => [p.componentId, p])
    );
    const newPartsMap = new Map(parts.map((p) => [p.componentId, p]));

    // Find added and removed parts
    parts.forEach((part) => {
      if (!oldPartsMap.has(part.componentId)) {
        changes.push({
          type: "added",
          partId: part.componentId,
          partMpn: part.mpn,
          newValue: part,
        });
      } else {
        const oldPart = oldPartsMap.get(part.componentId)!;
        if (oldPart.quantity !== part.quantity) {
          changes.push({
            type: "quantity_changed",
            partId: part.componentId,
            partMpn: part.mpn,
            oldValue: oldPart.quantity,
            newValue: part.quantity,
            field: "quantity",
          });
        }
        // Check for other field changes
        if (oldPart.price !== part.price) {
          changes.push({
            type: "modified",
            partId: part.componentId,
            partMpn: part.mpn,
            oldValue: oldPart.price,
            newValue: part.price,
            field: "price",
          });
        }
      }
    });

    oldPartsMap.forEach((oldPart, id) => {
      if (!newPartsMap.has(id)) {
        changes.push({
          type: "removed",
          partId: id,
          partMpn: oldPart.mpn,
          oldValue: oldPart,
        });
      }
    });

    const newVersion: BOMVersion = {
      version: newVersionNumber.toFixed(1),
      revision: newRevision,
      timestamp: new Date().toISOString(),
      author: "Current User", // Would come from auth context
      description: newVersionDescription || "BOM update",
      parts: [...parts],
      changes,
      approved: false,
    };

    setVersions([newVersion, ...versions]);
    setNewVersionDescription("");
    onVersionCreate?.(newVersion);
  };

  const selectedVersionData = useMemo(() => {
    if (!selectedVersion) return null;
    return versions.find((v) => `${v.version}-${v.revision}` === selectedVersion);
  }, [selectedVersion, versions]);

  const diffData = useMemo(() => {
    if (!selectedVersionData || !showDiff) return null;

    const currentPartsMap = new Map(parts.map((p) => [p.componentId, p]));
    const versionPartsMap = new Map(
      selectedVersionData.parts.map((p) => [p.componentId, p])
    );

    return {
      added: parts.filter((p) => !versionPartsMap.has(p.componentId)),
      removed: selectedVersionData.parts.filter(
        (p) => !currentPartsMap.has(p.componentId)
      ),
      modified: parts.filter((p) => {
        const oldPart = versionPartsMap.get(p.componentId);
        if (!oldPart) return false;
        return (
          oldPart.quantity !== p.quantity ||
          oldPart.price !== p.price ||
          oldPart.description !== p.description
        );
      }),
    };
  }, [selectedVersionData, parts, showDiff]);

  return (
    <div className="space-y-4">
      {/* Version Creation */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-neon-teal" />
            <h3 className="text-lg font-semibold text-white">BOM Versioning</h3>
            <Badge variant="outline" className="text-xs">
              v{currentVersion}
            </Badge>
          </div>
          <Button
            size="sm"
            onClick={createNewVersion}
            disabled={newVersionDescription.trim() === ""}
            className="bg-neon-teal hover:bg-neon-teal/80"
          >
            <Tag className="w-4 h-4 mr-2" />
            Create New Version
          </Button>
        </div>
        <input
          type="text"
          placeholder="Version description (e.g., 'Added power management components')"
          value={newVersionDescription}
          onChange={(e) => setNewVersionDescription(e.target.value)}
          className="w-full px-3 py-2 bg-dark-bg border border-dark-border rounded text-white placeholder-neutral-blue focus:outline-none focus:border-neon-teal"
        />
      </Card>

      {/* Version History */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center gap-2 mb-4">
          <History className="w-5 h-5 text-neutral-blue" />
          <h3 className="text-lg font-semibold text-white">Version History</h3>
        </div>
        <div className="space-y-2">
          {versions.map((version) => {
            const versionKey = `${version.version}-${version.revision}`;
            const isSelected = selectedVersion === versionKey;
            const isCurrent = version.version === currentVersion;

            return (
              <div
                key={versionKey}
                className={`p-3 rounded border ${
                  isSelected
                    ? "border-neon-teal bg-neon-teal/10"
                    : "border-dark-border bg-dark-bg"
                } ${isCurrent ? "ring-2 ring-neon-teal/50" : ""}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <Badge
                      variant={isCurrent ? "default" : "outline"}
                      className="text-xs"
                    >
                      v{version.version}-{version.revision}
                    </Badge>
                    {version.approved && (
                      <Badge variant="default" className="text-xs bg-green-500/20 text-green-400">
                        Approved
                      </Badge>
                    )}
                    <span className="text-sm text-white font-medium">
                      {version.description}
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        setSelectedVersion(isSelected ? null : versionKey);
                        setShowDiff(false);
                      }}
                      className="text-xs"
                    >
                      {isSelected ? "Hide" : "View"}
                    </Button>
                    {!isCurrent && (
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => onVersionRestore?.(version)}
                        className="text-xs"
                      >
                        Restore
                      </Button>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-4 text-xs text-neutral-blue">
                  <div className="flex items-center gap-1">
                    <User className="w-3 h-3" />
                    {version.author}
                  </div>
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(version.timestamp).toLocaleString()}
                  </div>
                  <div className="flex items-center gap-1">
                    <MessageSquare className="w-3 h-3" />
                    {version.changes.length} change(s)
                  </div>
                </div>
                {isSelected && (
                  <div className="mt-3 pt-3 border-t border-dark-border">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm text-neutral-blue">Changes:</span>
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => setShowDiff(!showDiff)}
                          className="text-xs"
                        >
                          <Diff className="w-3 h-3 mr-1" />
                          {showDiff ? "Hide" : "Show"} Diff
                        </Button>
                      </div>
                      {showDiff && diffData && (
                        <div className="space-y-2 mt-2">
                          {diffData.added.length > 0 && (
                            <div>
                              <div className="text-xs text-green-400 font-medium mb-1">
                                Added ({diffData.added.length}):
                              </div>
                              {diffData.added.map((part) => (
                                <div
                                  key={part.componentId}
                                  className="text-xs text-white bg-green-500/10 p-1 rounded"
                                >
                                  + {part.mpn}
                                </div>
                              ))}
                            </div>
                          )}
                          {diffData.removed.length > 0 && (
                            <div>
                              <div className="text-xs text-red-400 font-medium mb-1">
                                Removed ({diffData.removed.length}):
                              </div>
                              {diffData.removed.map((part) => (
                                <div
                                  key={part.componentId}
                                  className="text-xs text-white bg-red-500/10 p-1 rounded"
                                >
                                  - {part.mpn}
                                </div>
                              ))}
                            </div>
                          )}
                          {diffData.modified.length > 0 && (
                            <div>
                              <div className="text-xs text-yellow-400 font-medium mb-1">
                                Modified ({diffData.modified.length}):
                              </div>
                              {diffData.modified.map((part) => {
                                const oldPart = selectedVersionData!.parts.find(
                                  (p) => p.componentId === part.componentId
                                );
                                return (
                                  <div
                                    key={part.componentId}
                                    className="text-xs text-white bg-yellow-500/10 p-1 rounded"
                                  >
                                    ~ {part.mpn} (Qty: {oldPart?.quantity} →{" "}
                                    {part.quantity})
                                  </div>
                                );
                              })}
                            </div>
                          )}
                        </div>
                      )}
                      {!showDiff && (
                        <div className="text-xs text-neutral-blue">
                          {version.changes
                            .slice(0, 5)
                            .map((c) => {
                              const icons = {
                                added: "+",
                                removed: "-",
                                modified: "~",
                                quantity_changed: "±",
                              };
                              return `${icons[c.type]} ${c.partMpn}`;
                            })
                            .join(", ")}
                          {version.changes.length > 5 && "..."}
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </Card>
    </div>
  );
}

