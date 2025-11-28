import React, { useState } from "react";
import { Card } from "../../shared/components/ui/card";
import { Button } from "../../shared/components/ui/button";
import { Badge } from "../../shared/components/ui/badge";
import { 
  FileText, 
  Zap, 
  Wifi, 
  Cpu, 
  Battery,
  CheckCircle2,
  ArrowRight
} from "lucide-react";

interface DesignTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  icon: React.ReactNode;
  query: string;
  estimatedParts: number;
  estimatedCost: number;
  tags: string[];
}

const templates: DesignTemplate[] = [
  {
    id: "wifi-sensor",
    name: "WiFi Temperature Sensor",
    description: "IoT sensor board with WiFi connectivity and temperature sensing",
    category: "IoT",
    icon: <Wifi className="w-5 h-5" />,
    query: "WiFi temperature sensor board with ESP32, temperature sensor, and power management",
    estimatedParts: 12,
    estimatedCost: 15.50,
    tags: ["IoT", "WiFi", "Sensor"],
  },
  {
    id: "power-management",
    name: "Power Management Board",
    description: "Multi-rail power supply with battery charging and monitoring",
    category: "Power",
    icon: <Battery className="w-5 h-5" />,
    query: "Power management board with 5V and 3.3V regulators, battery charging, and power monitoring",
    estimatedParts: 18,
    estimatedCost: 22.00,
    tags: ["Power", "Battery", "Regulator"],
  },
  {
    id: "mcu-development",
    name: "MCU Development Board",
    description: "STM32 development board with USB, debug interface, and expansion headers",
    category: "Development",
    icon: <Cpu className="w-5 h-5" />,
    query: "STM32 development board with USB interface, debug connector, and expansion headers",
    estimatedParts: 25,
    estimatedCost: 28.50,
    tags: ["MCU", "Development", "STM32"],
  },
  {
    id: "motor-control",
    name: "Motor Control Board",
    description: "DC motor driver with current sensing and protection",
    category: "Control",
    icon: <Zap className="w-5 h-5" />,
    query: "DC motor control board with H-bridge driver, current sensing, and protection circuits",
    estimatedParts: 20,
    estimatedCost: 18.75,
    tags: ["Motor", "Control", "Driver"],
  },
];

interface DesignTemplatesProps {
  onTemplateSelect: (query: string) => void;
}

export default function DesignTemplates({ onTemplateSelect }: DesignTemplatesProps) {
  const [selectedCategory, setSelectedCategory] = useState<string>("all");

  const categories = ["all", ...Array.from(new Set(templates.map(t => t.category)))];

  const filteredTemplates = selectedCategory === "all"
    ? templates
    : templates.filter(t => t.category === selectedCategory);

  return (
    <Card className="p-4 bg-dark-surface border-dark-border">
      <div className="flex items-center gap-2 mb-4">
        <FileText className="w-5 h-5 text-blue-400" />
        <h3 className="text-lg font-semibold text-white">Design Templates</h3>
      </div>

      {/* Category Filter */}
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

      {/* Templates Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
        {filteredTemplates.map((template) => (
          <div
            key={template.id}
            className="p-4 rounded-lg bg-zinc-900/50 border border-zinc-800 hover:border-blue-500/50 transition-colors"
          >
            <div className="flex items-start justify-between mb-3">
              <div className="flex items-center gap-2">
                <div className="p-2 rounded bg-blue-500/20 text-blue-400">
                  {template.icon}
                </div>
                <div>
                  <h4 className="text-sm font-semibold text-white">{template.name}</h4>
                  <p className="text-xs text-zinc-400 mt-0.5">{template.category}</p>
                </div>
              </div>
            </div>

            <p className="text-xs text-zinc-300 mb-3">{template.description}</p>

            <div className="flex flex-wrap gap-1 mb-3">
              {template.tags.map((tag) => (
                <Badge
                  key={tag}
                  variant="outline"
                  className="text-xs border-zinc-700 text-zinc-400"
                >
                  {tag}
                </Badge>
              ))}
            </div>

            <div className="flex items-center justify-between text-xs text-zinc-400 mb-3">
              <span>~{template.estimatedParts} parts</span>
              <span>~${template.estimatedCost}</span>
            </div>

            <Button
              onClick={() => onTemplateSelect(template.query)}
              size="sm"
              className="w-full bg-blue-500 hover:bg-blue-600 text-white"
            >
              Use Template
              <ArrowRight className="w-4 h-4 ml-2" />
            </Button>
          </div>
        ))}
      </div>

      {filteredTemplates.length === 0 && (
        <div className="text-center py-8 text-zinc-400 text-sm">
          No templates found in this category
        </div>
      )}
    </Card>
  );
}

