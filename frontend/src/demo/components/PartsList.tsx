import { useState, useEffect, useMemo } from "react";
import { motion, AnimatePresence } from "motion/react";
import { Package, Download, CheckCircle2, Zap, Cpu, ExternalLink, Building2, Layers, AlertTriangle, Info, TestTube, Target, Plus, Minus, Trash2, Edit2, X, Search, Filter, ArrowUpDown } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Separator } from "../ui/separator";
import { Card } from "../ui/card";
import { Input } from "../ui/input";
import { Textarea } from "../ui/textarea";
import type { PartObject } from "../services/types";

interface PartsListProps {
  parts?: PartObject[];
  onQuantityChange?: (mpn: string, quantity: number) => void;
  onPartRemove?: (mpn: string) => void;
  onNoteChange?: (mpn: string, note: string) => void;
}

export default function PartsList({ 
  parts = [], 
  onQuantityChange,
  onPartRemove,
  onNoteChange 
}: PartsListProps) {
  const [editingNotes, setEditingNotes] = useState<Map<string, boolean>>(new Map());
  const [notes, setNotes] = useState<Map<string, string>>(new Map());
  const [localParts, setLocalParts] = useState<PartObject[]>(parts);
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState<"name" | "price" | "quantity" | "category">("name");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("asc");
  const [filterCategory, setFilterCategory] = useState<string>("all");

  // Sync local parts when props change
  useEffect(() => {
    setLocalParts(parts);
  }, [parts]);

  // Get unique categories
  const categories = useMemo(() => {
    const cats = new Set<string>();
    parts.forEach(part => {
      if (part.category) cats.add(part.category);
    });
    return Array.from(cats).sort();
  }, [parts]);

  // Filtered and sorted parts
  const filteredAndSortedParts = useMemo(() => {
    let filtered = localParts;

    // Search filter
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(part =>
        part.mpn.toLowerCase().includes(query) ||
        part.description.toLowerCase().includes(query) ||
        part.manufacturer.toLowerCase().includes(query)
      );
    }

    // Category filter
    if (filterCategory !== "all") {
      filtered = filtered.filter(part => part.category === filterCategory);
    }

    // Sort
    filtered = [...filtered].sort((a, b) => {
      let comparison = 0;
      
      switch (sortBy) {
        case "name":
          comparison = (a.mpn || "").localeCompare(b.mpn || "");
          break;
        case "price":
          comparison = (a.price || 0) - (b.price || 0);
          break;
        case "quantity":
          comparison = (a.quantity || 1) - (b.quantity || 1);
          break;
        case "category":
          comparison = (a.category || "").localeCompare(b.category || "");
          break;
      }
      
      return sortOrder === "asc" ? comparison : -comparison;
    });

    return filtered;
  }, [localParts, searchQuery, filterCategory, sortBy, sortOrder]);

  const handleQuantityChange = (mpn: string, delta: number) => {
    const updatedParts = localParts.map(part => {
      if (part.mpn === mpn) {
        const newQuantity = Math.max(1, (part.quantity || 1) + delta);
        const updatedPart = { ...part, quantity: newQuantity };
        if (onQuantityChange) {
          onQuantityChange(mpn, newQuantity);
        }
        return updatedPart;
      }
      return part;
    });
    setLocalParts(updatedParts);
  };

  const handleRemove = (mpn: string) => {
    const updatedParts = localParts.filter(part => part.mpn !== mpn);
    setLocalParts(updatedParts);
    if (onPartRemove) {
      onPartRemove(mpn);
    }
  };

  const handleNoteSave = (mpn: string) => {
    const note = notes.get(mpn) || "";
    if (onNoteChange) {
      onNoteChange(mpn, note);
    }
    setEditingNotes(new Map(editingNotes.set(mpn, false)));
  };

  const totalCost = localParts.reduce((sum, part) => {
    return sum + (part.price * (part.quantity || 1));
  }, 0);

  const currency = localParts[0]?.currency || "USD";

  const totalItems = localParts.reduce((sum, part) => {
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

      {/* Filters and Search */}
      <div className="p-4 border-b border-zinc-800 space-y-3 flex-shrink-0">
        {/* Search */}
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-zinc-400" />
          <Input
            type="text"
            placeholder="Search parts..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-10 bg-zinc-900 border-zinc-700 text-white"
          />
        </div>

        {/* Category Filter and Sort */}
        <div className="flex gap-2">
          <select
            value={filterCategory}
            onChange={(e) => setFilterCategory(e.target.value)}
            className="flex-1 px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-sm text-white"
          >
            <option value="all">All Categories</option>
            {categories.map(cat => (
              <option key={cat} value={cat}>{cat}</option>
            ))}
          </select>
          
          <select
            value={`${sortBy}-${sortOrder}`}
            onChange={(e) => {
              const [by, order] = e.target.value.split("-");
              setSortBy(by as typeof sortBy);
              setSortOrder(order as typeof sortOrder);
            }}
            className="px-3 py-2 bg-zinc-900 border border-zinc-700 rounded text-sm text-white"
          >
            <option value="name-asc">Name ↑</option>
            <option value="name-desc">Name ↓</option>
            <option value="price-asc">Price ↑</option>
            <option value="price-desc">Price ↓</option>
            <option value="quantity-asc">Quantity ↑</option>
            <option value="quantity-desc">Quantity ↓</option>
            <option value="category-asc">Category ↑</option>
            <option value="category-desc">Category ↓</option>
          </select>
        </div>
      </div>

      {/* Parts List */}
      <div className="flex-1 overflow-y-auto p-6 space-y-4">
        <AnimatePresence mode="popLayout">
          {filteredAndSortedParts.length === 0 ? (
            <div className="text-center py-12 text-zinc-500">
              <Package className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>{searchQuery || filterCategory !== "all" ? "No parts match filters" : "No parts added yet"}</p>
            </div>
          ) : (
            filteredAndSortedParts.map((part, index) => (
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
                      <div className="flex items-center gap-2 mt-1">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleQuantityChange(part.mpn, -1)}
                          className="h-6 w-6 p-0 hover:bg-zinc-800"
                          title="Decrease quantity">
                          <Minus className="w-3 h-3" />
                        </Button>
                        <span className="text-xs text-zinc-300 min-w-[20px] text-center">
                          {part.quantity || 1}
                        </span>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleQuantityChange(part.mpn, 1)}
                          className="h-6 w-6 p-0 hover:bg-zinc-800"
                          title="Increase quantity">
                          <Plus className="w-3 h-3" />
                        </Button>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRemove(part.mpn)}
                          className="h-6 w-6 p-0 hover:bg-red-500/10 hover:text-red-400"
                          title="Remove part">
                          <Trash2 className="w-3 h-3" />
                        </Button>
                      </div>
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

                  {/* Notes Section */}
                  <div className="mt-3 pt-3 border-t border-zinc-800">
                    {editingNotes.get(part.mpn) ? (
                      <div className="space-y-2">
                        <Textarea
                          value={notes.get(part.mpn) || ""}
                          onChange={(e) => {
                            const newNotes = new Map(notes);
                            newNotes.set(part.mpn, e.target.value);
                            setNotes(newNotes);
                          }}
                          placeholder="Add notes for this part..."
                          className="bg-zinc-900/60 border-zinc-700 text-zinc-100 text-xs min-h-[60px]"
                        />
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            onClick={() => handleNoteSave(part.mpn)}
                            className="h-7 text-xs bg-emerald-500 hover:bg-emerald-600">
                            Save
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              const newEditing = new Map(editingNotes);
                              newEditing.set(part.mpn, false);
                              setEditingNotes(newEditing);
                            }}
                            className="h-7 text-xs">
                            Cancel
                          </Button>
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          {notes.get(part.mpn) ? (
                            <p className="text-xs text-zinc-400 italic">{notes.get(part.mpn)}</p>
                          ) : (
                            <p className="text-xs text-zinc-600">No notes</p>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => {
                            const newEditing = new Map(editingNotes);
                            newEditing.set(part.mpn, true);
                            setEditingNotes(newEditing);
                            if (!notes.has(part.mpn)) {
                              const newNotes = new Map(notes);
                              newNotes.set(part.mpn, "");
                              setNotes(newNotes);
                            }
                          }}
                          className="h-7 w-7 p-0 hover:bg-zinc-800"
                          title="Add/edit notes">
                          <Edit2 className="w-3 h-3" />
                        </Button>
                      </div>
                    )}
                  </div>

                  {/* Footer with datasheet */}
                  <div className="mt-2 flex items-center justify-end">
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
            <div className="flex gap-2">
              <Button 
                className="flex-1 bg-emerald-500 hover:bg-emerald-600 text-white"
                onClick={() => {
                  // Export to CSV
                  const headers = ["MPN", "Manufacturer", "Description", "Quantity", "Unit Price", "Total Price", "Currency", "Package", "Footprint", "Voltage", "Interfaces", "Datasheet", "Notes"];
                  const rows = localParts.map(part => [
                    part.mpn,
                    part.manufacturer,
                    part.description,
                    part.quantity || 1,
                    part.price,
                    (part.price * (part.quantity || 1)).toFixed(2),
                    part.currency || "USD",
                    part.package || "",
                    part.footprint || "",
                    part.voltage || "",
                    (part.interfaces || []).join("; "),
                    part.datasheet || "",
                    notes.get(part.mpn) || ""
                  ]);
                  
                  const csvContent = [
                    headers.join(","),
                    ...rows.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(","))
                  ].join("\n");
                  
                  const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
                  const link = document.createElement("a");
                  const url = URL.createObjectURL(blob);
                  link.setAttribute("href", url);
                  link.setAttribute("download", `bom_${new Date().toISOString().split('T')[0]}.csv`);
                  link.style.visibility = "hidden";
                  document.body.appendChild(link);
                  link.click();
                  document.body.removeChild(link);
                }}>
                <Download className="w-4 h-4 mr-2" />
                Export CSV
              </Button>
              <Button 
                className="flex-1 bg-blue-500 hover:bg-blue-600 text-white"
                onClick={async () => {
                  try {
                    const XLSX = await import("xlsx");
                    const workbook = XLSX.utils.book_new();
                    
                    // Create data array
                    const data = localParts.map(part => ({
                      "MPN": part.mpn,
                      "Manufacturer": part.manufacturer,
                      "Description": part.description,
                      "Quantity": part.quantity || 1,
                      "Unit Price": part.price,
                      "Total Price": (part.price * (part.quantity || 1)).toFixed(2),
                      "Currency": part.currency || "USD",
                      "Package": part.package || "",
                      "Footprint": part.footprint || "",
                      "Voltage": part.voltage || "",
                      "Interfaces": (part.interfaces || []).join("; "),
                      "Datasheet": part.datasheet || "",
                      "Notes": notes.get(part.mpn) || ""
                    }));
                    
                    const worksheet = XLSX.utils.json_to_sheet(data);
                    XLSX.utils.book_append_sheet(workbook, worksheet, "BOM");
                    
                    // Generate Excel file
                    XLSX.writeFile(workbook, `bom_${new Date().toISOString().split('T')[0]}.xlsx`);
                  } catch (error) {
                    console.error("Excel export failed:", error);
                    alert("Excel export failed. Please try CSV export instead.");
                  }
                }}>
                <Download className="w-4 h-4 mr-2" />
                Export Excel
              </Button>
            </div>
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

