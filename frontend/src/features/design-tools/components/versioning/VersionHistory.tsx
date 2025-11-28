/**
 * Version History Component
 * Design versioning and history management
 */

import React, { useState } from "react";
import { Card } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import {
  History,
  GitBranch,
  Tag,
  Clock,
  User,
  Download,
  RotateCcw,
  Eye,
} from "lucide-react";

interface Version {
  id: string;
  version: string;
  timestamp: string;
  author?: string;
  description: string;
  partsCount: number;
  tag?: string;
}

interface VersionHistoryProps {
  versions: Version[];
  currentVersionId?: string;
  onVersionSelect?: (version: Version) => void;
  onVersionRestore?: (version: Version) => void;
  onVersionExport?: (version: Version) => void;
}

export default function VersionHistory({
  versions,
  currentVersionId,
  onVersionSelect,
  onVersionRestore,
  onVersionExport,
}: VersionHistoryProps) {
  const [selectedVersion, setSelectedVersion] = useState<string | null>(null);

  const sortedVersions = [...versions].sort(
    (a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
  );

  return (
    <Card className="bg-dark-surface border-dark-border p-4">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <History className="w-5 h-5 text-neutral-blue" />
          <h3 className="text-lg font-semibold text-white">Version History</h3>
          <Badge variant="outline" className="text-xs">
            {versions.length} versions
          </Badge>
        </div>
      </div>

      <div className="space-y-2 max-h-[600px] overflow-y-auto">
        {sortedVersions.map((version) => (
          <div
            key={version.id}
            className={`p-3 rounded border transition-all ${
              version.id === currentVersionId
                ? "bg-neon-teal/10 border-neon-teal"
                : selectedVersion === version.id
                ? "bg-zinc-900/50 border-zinc-700"
                : "bg-dark-bg border-dark-border hover:border-zinc-700"
            }`}
            onClick={() => {
              setSelectedVersion(version.id);
              onVersionSelect?.(version);
            }}
          >
            <div className="flex items-start justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-sm font-medium text-white">
                    {version.version}
                  </span>
                  {version.id === currentVersionId && (
                    <Badge variant="default" className="text-xs">
                      Current
                    </Badge>
                  )}
                  {version.tag && (
                    <Badge variant="outline" className="text-xs">
                      <Tag className="w-3 h-3 mr-1" />
                      {version.tag}
                    </Badge>
                  )}
                </div>
                <p className="text-xs text-neutral-blue mb-2">
                  {version.description}
                </p>
                <div className="flex items-center gap-4 text-xs text-neutral-blue">
                  <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(version.timestamp).toLocaleString()}
                  </div>
                  {version.author && (
                    <div className="flex items-center gap-1">
                      <User className="w-3 h-3" />
                      {version.author}
                    </div>
                  )}
                  <div>{version.partsCount} parts</div>
                </div>
              </div>
              <div className="flex items-center gap-1 ml-4">
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    onVersionSelect?.(version);
                  }}
                  className="h-7 w-7 p-0"
                >
                  <Eye className="w-4 h-4" />
                </Button>
                {version.id !== currentVersionId && (
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={(e) => {
                      e.stopPropagation();
                      onVersionRestore?.(version);
                    }}
                    className="h-7 w-7 p-0"
                  >
                    <RotateCcw className="w-4 h-4" />
                  </Button>
                )}
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={(e) => {
                    e.stopPropagation();
                    onVersionExport?.(version);
                  }}
                  className="h-7 w-7 p-0"
                >
                  <Download className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

