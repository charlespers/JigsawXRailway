import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Settings, X, Save } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";

interface SettingsPanelProps {
  backendUrl: string;
  defaultProvider: "openai" | "xai";
  onBackendUrlChange?: (url: string) => void;
  onProviderChange?: (provider: "openai" | "xai") => void;
}

export default function SettingsPanel({
  backendUrl,
  defaultProvider,
  onBackendUrlChange,
  onProviderChange,
}: SettingsPanelProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [localBackendUrl, setLocalBackendUrl] = useState(backendUrl);
  const [localProvider, setLocalProvider] = useState<"openai" | "xai">(defaultProvider);

  useEffect(() => {
    setLocalBackendUrl(backendUrl);
    setLocalProvider(defaultProvider);
  }, [backendUrl, defaultProvider]);

  const handleSave = () => {
    if (onBackendUrlChange) {
      onBackendUrlChange(localBackendUrl);
    }
    if (onProviderChange) {
      onProviderChange(localProvider);
    }
    // Save to localStorage
    localStorage.setItem("demo_backend_url", localBackendUrl);
    localStorage.setItem("demo_provider", localProvider);
    setIsOpen(false);
  };

  return (
    <>
      {/* Settings Button */}
      <button
        onClick={() => setIsOpen(true)}
        className="fixed top-4 right-4 z-50 p-2 bg-zinc-900/80 border border-zinc-800 rounded-lg hover:bg-zinc-800 transition-colors"
        title="Settings">
        <Settings className="w-5 h-5 text-zinc-400" />
      </button>

      {/* Settings Panel */}
      <AnimatePresence>
        {isOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setIsOpen(false)}
              className="fixed inset-0 bg-black/50 z-50"
            />
            {/* Panel */}
            <motion.div
              initial={{ x: 400, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: 400, opacity: 0 }}
              className="fixed right-0 top-0 h-full w-96 bg-zinc-900 border-l border-zinc-800 z-50 flex flex-col">
              <div className="p-6 border-b border-zinc-800 flex items-center justify-between">
                <h2 className="text-lg font-semibold">Settings</h2>
                <button
                  onClick={() => setIsOpen(false)}
                  className="p-1 hover:bg-zinc-800 rounded">
                  <X className="w-5 h-5" />
                </button>
              </div>

              <div className="flex-1 overflow-y-auto p-6 space-y-6">
                {/* Backend URL */}
                <div>
                  <label className="block text-sm font-medium mb-2 text-zinc-300">
                    Backend URL
                  </label>
                  <Input
                    value={localBackendUrl}
                    onChange={(e) => setLocalBackendUrl(e.target.value)}
                    placeholder="http://localhost:3001"
                    className="bg-zinc-800 border-zinc-700 text-zinc-100"
                  />
                  <p className="text-xs text-zinc-500 mt-1">
                    API endpoint for component analysis
                  </p>
                </div>

                {/* Provider */}
                <div>
                  <label className="block text-sm font-medium mb-2 text-zinc-300">
                    Default AI Provider
                  </label>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setLocalProvider("openai")}
                      className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                        localProvider === "openai"
                          ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                          : "bg-zinc-800 border-zinc-700 text-zinc-300 hover:bg-zinc-700"
                      }`}>
                      OpenAI
                    </button>
                    <button
                      onClick={() => setLocalProvider("xai")}
                      className={`flex-1 px-4 py-2 rounded-lg border transition-colors ${
                        localProvider === "xai"
                          ? "bg-emerald-500/20 border-emerald-500 text-emerald-400"
                          : "bg-zinc-800 border-zinc-700 text-zinc-300 hover:bg-zinc-700"
                      }`}>
                      XAI (Grok)
                    </button>
                  </div>
                  <p className="text-xs text-zinc-500 mt-1">
                    Default provider for new queries (can be changed per query)
                  </p>
                </div>
              </div>

              <div className="p-6 border-t border-zinc-800">
                <Button
                  onClick={handleSave}
                  className="w-full bg-emerald-500 hover:bg-emerald-600">
                  <Save className="w-4 h-4 mr-2" />
                  Save Settings
                </Button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}

