/**
 * Share Dialog Component
 * Share designs with permissions
 */

import React, { useState } from "react";
import { Card } from "../../ui/card";
import { Button } from "../../ui/button";
import { Badge } from "../../ui/badge";
import {
  Share2,
  Copy,
  Mail,
  Link,
  Lock,
  Globe,
  Users,
  X,
  Check,
} from "lucide-react";

interface ShareDialogProps {
  designId: string;
  onClose: () => void;
  onShare?: (settings: ShareSettings) => void;
}

interface ShareSettings {
  public: boolean;
  allowEdit: boolean;
  allowComment: boolean;
  expiresAt?: string;
}

export default function ShareDialog({
  designId,
  onClose,
  onShare,
}: ShareDialogProps) {
  const [shareSettings, setShareSettings] = useState<ShareSettings>({
    public: false,
    allowEdit: false,
    allowComment: true,
  });
  const [shareLink, setShareLink] = useState("");
  const [copied, setCopied] = useState(false);

  const generateShareLink = () => {
    const baseUrl = window.location.origin;
    const link = `${baseUrl}/design/${designId}?shared=true`;
    setShareLink(link);
    
    if (onShare) {
      onShare(shareSettings);
    }
  };

  const copyToClipboard = () => {
    if (shareLink) {
      navigator.clipboard.writeText(shareLink);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <Card className="w-full max-w-md bg-dark-surface border-dark-border p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-2">
            <Share2 className="w-5 h-5 text-neutral-blue" />
            <h2 className="text-xl font-semibold text-white">Share Design</h2>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={onClose}
            className="text-neutral-blue hover:text-white"
          >
            <X className="w-5 h-5" />
          </Button>
        </div>

        <div className="space-y-4">
          {/* Share Settings */}
          <div className="space-y-3">
            <div className="flex items-center justify-between p-3 bg-dark-bg rounded border border-dark-border">
              <div className="flex items-center gap-2">
                <Globe className="w-4 h-4 text-neutral-blue" />
                <span className="text-sm text-white">Public Link</span>
              </div>
              <input
                type="checkbox"
                checked={shareSettings.public}
                onChange={(e) =>
                  setShareSettings({ ...shareSettings, public: e.target.checked })
                }
                className="rounded"
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-dark-bg rounded border border-dark-border">
              <div className="flex items-center gap-2">
                <Users className="w-4 h-4 text-neutral-blue" />
                <span className="text-sm text-white">Allow Editing</span>
              </div>
              <input
                type="checkbox"
                checked={shareSettings.allowEdit}
                onChange={(e) =>
                  setShareSettings({
                    ...shareSettings,
                    allowEdit: e.target.checked,
                  })
                }
                className="rounded"
              />
            </div>

            <div className="flex items-center justify-between p-3 bg-dark-bg rounded border border-dark-border">
              <div className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-neutral-blue" />
                <span className="text-sm text-white">Allow Comments</span>
              </div>
              <input
                type="checkbox"
                checked={shareSettings.allowComment}
                onChange={(e) =>
                  setShareSettings({
                    ...shareSettings,
                    allowComment: e.target.checked,
                  })
                }
                className="rounded"
              />
            </div>
          </div>

          {/* Share Link */}
          {shareLink && (
            <div className="p-3 bg-dark-bg rounded border border-dark-border">
              <div className="flex items-center gap-2 mb-2">
                <Link className="w-4 h-4 text-neutral-blue" />
                <span className="text-xs text-neutral-blue">Share Link</span>
              </div>
              <div className="flex items-center gap-2">
                <input
                  type="text"
                  value={shareLink}
                  readOnly
                  className="flex-1 px-2 py-1 bg-zinc-900 border border-dark-border rounded text-white text-sm"
                />
                <Button
                  size="sm"
                  variant="outline"
                  onClick={copyToClipboard}
                  className="text-xs"
                >
                  {copied ? (
                    <>
                      <Check className="w-4 h-4 mr-1" />
                      Copied
                    </>
                  ) : (
                    <>
                      <Copy className="w-4 h-4 mr-1" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex items-center justify-end gap-2 pt-4 border-t border-dark-border">
            <Button variant="outline" onClick={onClose}>
              Cancel
            </Button>
            <Button
              onClick={generateShareLink}
              className="bg-neon-teal hover:bg-neon-teal/80 text-dark-bg"
            >
              <Share2 className="w-4 h-4 mr-2" />
              Generate Link
            </Button>
          </div>
        </div>
      </Card>
    </div>
  );
}

