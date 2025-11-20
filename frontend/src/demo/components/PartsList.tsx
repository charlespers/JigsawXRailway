import { motion, AnimatePresence } from "motion/react";
import { Package, Download, CheckCircle2, Zap, Cpu, ExternalLink, Building2, Layers, AlertTriangle, Info, TestTube, Target } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { Card } from "../ui/card";
import type { PartObject } from "../services/types";

interface PartsListProps {
  parts?: PartObject[];
}

export default function PartsList({ parts = [] }: PartsListProps) {
  const totalCost = parts.reduce((sum, part) => {
    return sum + (part.price * (part.quantity || 1));
  }, 0);

  const currency = parts[0]?.currency || "USD";

  const totalItems = parts.reduce((sum, part) => {
    return sum + (part.quantity || 1);
  }, 0);

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-zinc-800 flex-shrink-0">
        <div className="flex items-center gap-2 mb-2">
          <Package className="w-5 h-5 text-emerald-400" />
          <h2 className="text-lg">Parts List</h2>
        </div>
        <p className="text-sm text-zinc-400">
          Component specifications and pricing
        </p>
      </div>

      {/* Parts List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        <AnimatePresence mode="popLayout">
          {parts.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>No parts added yet</p>
            </div>
          ) : (
            parts.map((part, index) => (
              <motion.div
                key={`${part.mpn}-${index}`}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                transition={{ delay: index * 0.1 }}>
                <Card className="bg-zinc-900/50 border-zinc-800 p-4">
                  {/* Part Name and Price */}
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1 min-w-0">
                      <h3 className="text-sm font-medium mb-1 truncate">
                        {part.mpn}
                      </h3>
                      <div className="flex items-center gap-2 mb-1">
                        <Building2 className="w-3 h-3 text-zinc-500" />
                        <p className="text-xs text-zinc-500">
                          {part.manufacturer}
                        </p>
                      </div>
                      <p className="text-xs text-zinc-400 mb-2 line-clamp-2">
                        {part.description}
                      </p>
                    </div>
                    <div className="text-right ml-4 flex-shrink-0">
                      <div className="text-lg font-semibold text-emerald-400">
                        {part.currency || "USD"} {part.price.toFixed(2)}
                      </div>
                      {part.quantity && part.quantity > 1 && (
                        <div className="text-xs text-zinc-500">
                          x{part.quantity}
                        </div>
                      )}
                    </div>
                  </div>

                  {/* Specifications */}
                  <div className="space-y-2">
                    {part.voltage && (
                      <div className="flex items-center gap-2 text-xs">
                        <Zap className="w-3 h-3 text-zinc-500" />
                        <span className="text-zinc-400">
                          <span className="text-zinc-500">Voltage:</span> {part.voltage}
                        </span>
                      </div>
                    )}
                    {part.package && (
                      <div className="flex items-center gap-2 text-xs">
                        <Package className="w-3 h-3 text-zinc-500" />
                        <span className="text-zinc-400">
                          <span className="text-zinc-500">Package:</span> {part.package}
                        </span>
                      </div>
                    )}
                    {part.footprint && (
                      <div className="flex items-center gap-2 text-xs">
                        <Layers className="w-3 h-3 text-zinc-500" />
                        <span className="text-zinc-400">
                          <span className="text-zinc-500">Footprint:</span> {part.footprint}
                        </span>
                      </div>
                    )}
                    {part.interfaces && part.interfaces.length > 0 && (
                      <div className="flex items-start gap-2 text-xs">
                        <Cpu className="w-3 h-3 text-zinc-500 mt-0.5" />
                        <div className="flex-1">
                          <span className="text-zinc-500">Interfaces: </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {part.interfaces.map((iface, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-xs border-zinc-700 text-zinc-400 px-1.5 py-0">
                                {iface}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                    {part.assembly_side && (
                      <div className="flex items-center gap-2 text-xs">
                        <Layers className="w-3 h-3 text-zinc-500" />
                        <span className="text-zinc-400">
                          <span className="text-zinc-500">Assembly Side:</span> {part.assembly_side}
                        </span>
                      </div>
                    )}
                    {part.msl_level && (
                      <div className="flex items-center gap-2 text-xs">
                        <AlertTriangle className="w-3 h-3 text-amber-500" />
                        <span className="text-zinc-400">
                          <span className="text-zinc-500">MSL Level:</span> {part.msl_level}
                        </span>
                      </div>
                    )}
                    {part.temperature_rating && (
                      <div className="flex items-center gap-2 text-xs">
                        <Zap className="w-3 h-3 text-zinc-500" />
                        <span className="text-zinc-400">
                          <span className="text-zinc-500">Temp Rating:</span> {part.temperature_rating}
                        </span>
                      </div>
                    )}
                    {part.tolerance && (
                      <div className="flex items-center gap-2 text-xs">
                        <Info className="w-3 h-3 text-zinc-500" />
                        <span className="text-zinc-400">
                          <span className="text-zinc-500">Tolerance:</span> {part.tolerance}
                        </span>
                      </div>
                    )}
                    {part.assembly_notes && (
                      <div className="flex items-start gap-2 text-xs mt-2 p-2 bg-amber-500/10 border border-amber-500/20 rounded">
                        <Info className="w-3 h-3 text-amber-400 mt-0.5 flex-shrink-0" />
                        <div className="flex-1">
                          <span className="text-amber-400 font-medium">Assembly Notes: </span>
                          <span className="text-zinc-400">{part.assembly_notes}</span>
                        </div>
                      </div>
                    )}
                    {part.alternate_part_numbers && part.alternate_part_numbers.length > 0 && (
                      <div className="flex items-start gap-2 text-xs">
                        <Package className="w-3 h-3 text-zinc-500 mt-0.5" />
                        <div className="flex-1">
                          <span className="text-zinc-500">Alternates: </span>
                          <div className="flex flex-wrap gap-1 mt-1">
                            {part.alternate_part_numbers.map((alt, idx) => (
                              <Badge
                                key={idx}
                                variant="outline"
                                className="text-xs border-zinc-700 text-zinc-400 px-1.5 py-0">
                                {alt}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  {/* Special Component Indicators */}
                  {(part.test_point || part.fiducial) && (
                    <div className="mt-2 flex gap-2">
                      {part.test_point && (
                        <Badge variant="outline" className="text-xs border-blue-500/50 text-blue-400 bg-blue-500/10">
                          <TestTube className="w-3 h-3 mr-1" />
                          Test Point
                        </Badge>
                      )}
                      {part.fiducial && (
                        <Badge variant="outline" className="text-xs border-purple-500/50 text-purple-400 bg-purple-500/10">
                          <Target className="w-3 h-3 mr-1" />
                          Fiducial
                        </Badge>
                      )}
                    </div>
                  )}
                  
                  {/* Lifecycle & Compliance */}
                  <div className="mt-2 flex flex-wrap gap-2">
                    {part.lifecycle_status && (
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          part.lifecycle_status === "active"
                            ? "border-emerald-500/50 text-emerald-400 bg-emerald-500/10"
                            : "border-amber-500/50 text-amber-400 bg-amber-500/10"
                        }`}>
                        {part.lifecycle_status}
                      </Badge>
                    )}
                    {part.rohs_compliant && (
                      <Badge variant="outline" className="text-xs border-green-500/50 text-green-400 bg-green-500/10">
                        RoHS
                      </Badge>
                    )}
                    {part.availability_status && (
                      <Badge
                        variant="outline"
                        className={`text-xs ${
                          part.availability_status === "in_stock"
                            ? "border-emerald-500/50 text-emerald-400 bg-emerald-500/10"
                            : "border-red-500/50 text-red-400 bg-red-500/10"
                        }`}>
                        {part.availability_status === "in_stock" ? "In Stock" : part.availability_status}
                      </Badge>
                    )}
                    {part.lead_time_days && (
                      <Badge variant="outline" className="text-xs border-zinc-700 text-zinc-400">
                        {part.lead_time_days}d lead time
                      </Badge>
                    )}
                  </div>

                  {/* Footer with quantity and datasheet */}
                  <div className="mt-3 pt-3 border-t border-zinc-800 flex items-center justify-between">
                    {part.quantity && part.quantity > 1 && (
                      <Badge
                        variant="outline"
                        className="text-xs border-zinc-700 text-zinc-400">
                        Quantity: {part.quantity}
                      </Badge>
                    )}
                    {part.datasheet && (
                      <a
                        href={part.datasheet}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-emerald-400 hover:text-emerald-300 transition-colors">
                        <ExternalLink className="w-3 h-3" />
                        Datasheet
                      </a>
                    )}
                  </div>
                </Card>
              </motion.div>
            ))
          )}
        </AnimatePresence>
      </div>

      {/* Summary Footer */}
      {parts.length > 0 && (
        <motion.div
          initial={{ y: 20, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          className="border-t border-zinc-800 bg-zinc-900/50 p-6 flex-shrink-0">
          <div className="space-y-4">
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-400">Total Items</span>
              <span className="text-white">{totalItems} items</span>
            </div>
            <div className="flex items-center justify-between text-sm">
              <span className="text-zinc-400">Parts Count</span>
              <span className="text-white">{parts.length} parts</span>
            </div>
            <Separator className="bg-zinc-800" />
            <div className="flex items-center justify-between">
              <span className="text-lg">Total Cost</span>
              <span className="text-2xl text-emerald-400">
                {currency} {totalCost.toFixed(2)}
              </span>
            </div>
            <div className="text-xs text-zinc-500 text-center">
              Unit price • Bulk discounts available
            </div>
            <Button className="w-full bg-emerald-500 hover:bg-emerald-600 text-white">
              <Download className="w-4 h-4 mr-2" />
              Export Parts List
            </Button>
            <div className="flex items-center justify-center gap-2 text-xs text-zinc-400">
              <CheckCircle2 className="w-3 h-3 text-emerald-400" />
              <span>All parts verified compatible</span>
            </div>
          </div>
        </motion.div>
      )}
    </div>
  );
}

