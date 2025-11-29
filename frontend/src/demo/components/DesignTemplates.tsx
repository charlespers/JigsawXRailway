import React, { useState, useEffect } from "react";
import { Card } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { 
  FileText, 
  Zap, 
  Wifi, 
  Cpu, 
  Battery,
  CheckCircle2,
  ArrowRight,
  Loader2
} from "lucide-react";
import { fetchTemplates, generateFromTemplate, type DesignTemplate } from "../services/designApi";

interface DesignTemplatesProps {
  onTemplateSelect: (query: string) => void;
  onTemplateGenerate?: (templateId: string, parts: Record<string, any>) => void;
}

const iconMap: Record<string, React.ReactNode> = {
  "IoT": <Wifi className="w-5 h-5" />,
  "Power": <Battery className="w-5 h-5" />,
  "Development": <Cpu className="w-5 h-5" />,
  "Control": <Zap className="w-5 h-5" />,
  "default": <FileText className="w-5 h-5" />
};

export default function DesignTemplates({ onTemplateSelect, onTemplateGenerate }: DesignTemplatesProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");
  const [templates, setTemplates] = useState<DesignTemplate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [generating, setGenerating] = useState<string | null>(null);

  useEffect(() => {
    loadTemplates();
  }, []);

  const loadTemplates = async () => {
    try {
      setLoading(true);
      setError(null);
      const fetchedTemplates = await fetchTemplates();
      setTemplates(fetchedTemplates);
    } catch (err) {
      console.error("Failed to load templates:", err);
      setError(err instanceof Error ? err.message : "Failed to load templates");
      // Fallback to hardcoded templates if API fails
      setTemplates([]);
    } finally {
      setLoading(false);
    }
  };

  const handleTemplateClick = async (template: DesignTemplate) => {
    if (onTemplateGenerate) {
      // Try to generate from template API
      try {
        setGenerating(template.id);
        const result = await generateFromTemplate(template.id);
        if (result.success && result.selected_parts) {
          onTemplateGenerate(template.id, result.selected_parts);
          return;
        }
      } catch (err) {
        console.error("Template generation failed, falling back to query:", err);
      } finally {
        setGenerating(null);
      }
    }
    
    // Fallback: use query string
    const query = template.requirements?.functional_requirements?.join(", ") || 
                  template.description || 
                  `Design a ${template.name.toLowerCase()}`;
    onTemplateSelect(query);
  };

  const categories = ["all", ...Array.from(new Set(templates.map(t => t.category)))];

  const filteredTemplates = selectedCategory === "all"
    ? templates
    : templates.filter(t => t.category === selectedCategory);

  if (loading) {
    return (
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center justify-center py-8">
          <Loader2 className="w-6 h-6 text-blue-400 animate-spin" />
          <span className="ml-2 text-neutral-blue">Loading templates...</span>
        </div>
      </Card>
    );
  }

  if (error && templates.length === 0) {
    return (
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="text-center py-8 text-red-400 text-sm">
          {error}
        </div>
      </Card>
    );
  }

  return (
    <Card className="p-4 bg-dark-surface border-dark-border">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <FileText className="w-5 h-5 text-blue-400" />
          <h3 className="text-lg font-semibold text-white">Design Templates</h3>
        </div>
        <Button
          size="sm"
          variant="ghost"
          onClick={loadTemplates}
          className="text-xs"
        >
          Refresh
        </Button>
      </div>

      {/* Category Filter */}
      {categories.length > 1 && (
        <div className="flex gap-2 mb-4 flex-wrap">
          {categories.map((category) => (
            <button
              key={category}
              onClick={() => setSelectedCategory(category)}
              className={`px-3 py-1.5 rounded text-xs font-medium transition-colors ${
                selectedCategory === category
                  ? "bg-blue-500/20 text-blue-400 border border-blue-500/50"
                  : "bg-zinc-800 text-zinc-400 hover:bg-zinc-700"
              }`}
            >
              {category.charAt(0).toUpperCase() + category.slice(1)}
            </button>
          ))}
        </div>
      )}

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filteredTemplates.map((template) => {
          const icon = iconMap[template.category] || iconMap.default;
          const estimatedParts = template.parts_needed?.length || 0;
          
          return (
            <div
              key={template.id}
              className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 hover:border-blue-500/50 transition-colors"
            >
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <div className="p-2 rounded bg-blue-500/20 text-blue-400">
                    {icon}
                  </div>
                  <div>
                    <h4 className="text-sm font-semibold text-white">{template.name}</h4>
                    <p className="text-xs text-zinc-400 mt-0.5">{template.category}</p>
                  </div>
                </div>
              </div>

              <p className="text-xs text-zinc-300 mb-3">{template.description}</p>

              {estimatedParts > 0 && (
                <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
                  <span>~{estimatedParts} parts</span>
                </div>
              )}

              <Button
                onClick={() => handleTemplateClick(template)}
                size="sm"
                className="w-full bg-blue-500 hover:bg-blue-600 text-white"
                disabled={generating === template.id}
              >
                {generating === template.id ? (
                  <>
                    <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                    Generating...
                  </>
                ) : (
                  <>
                    Use Template
                    <ArrowRight className="w-4 h-4 ml-2" />
                  </>
                )}
              </Button>
            </div>
          );
        })}
      </div>

      {filteredTemplates.length === 0 && !loading && (
        <div className="text-center py-8 text-zinc-400 text-sm">
          No templates found in this category
        </div>
      )}
    </Card>
  );
}

