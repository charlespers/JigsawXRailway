/**
 * BOM Supplier Management and Price Comparison
 * Enterprise-level supplier management with multi-source pricing
 */

import React, { useState, useMemo } from "react";
import { Card } from "../../../shared/components/ui/card";
import { Button } from "../../../shared/components/ui/button";
import { Badge } from "../../../shared/components/ui/badge";
import {
  ShoppingCart,
  DollarSign,
  TrendingDown,
  TrendingUp,
  ExternalLink,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Package,
} from "lucide-react";
import type { PartObject } from "../../../shared/services/types";
import { normalizePrice, normalizeQuantity } from "../../utils/partNormalizer";

interface Supplier {
  name: string;
  url: string;
  partNumber: string;
  price: number;
  quantity: number; // MOQ
  leadTimeDays: number;
  inStock: boolean;
  rating: number;
  lastUpdated: string;
}

interface SupplierData {
  [mpn: string]: Supplier[];
}

interface BOMSupplierManagementProps {
  parts: PartObject[];
  onSupplierSelect?: (mpn: string, supplier: Supplier) => void;
}

const MOCK_SUPPLIERS: SupplierData = {
  "ESP32-S3-WROOM-1": [
    {
      name: "DigiKey",
      url: "https://www.digikey.com/en/products/detail/espressif-systems/ESP32-S3-WROOM-1/12345678",
      partNumber: "ESP32-S3-WROOM-1-ND",
      price: 2.50,
      quantity: 1,
      leadTimeDays: 0,
      inStock: true,
      rating: 4.8,
      lastUpdated: new Date().toISOString(),
    },
    {
      name: "Mouser",
      url: "https://www.mouser.com/ProductDetail/Espressif/ESP32-S3-WROOM-1",
      partNumber: "ESP32-S3-WROOM-1",
      price: 2.45,
      quantity: 1,
      leadTimeDays: 0,
      inStock: true,
      rating: 4.7,
      lastUpdated: new Date().toISOString(),
    },
    {
      name: "LCSC",
      url: "https://www.lcsc.com/product-detail/ESP32-S3-WROOM-1",
      partNumber: "C123456",
      price: 1.80,
      quantity: 10,
      leadTimeDays: 7,
      inStock: true,
      rating: 4.5,
      lastUpdated: new Date().toISOString(),
    },
  ],
  "TMP102": [
    {
      name: "DigiKey",
      url: "https://www.digikey.com/en/products/detail/texas-instruments/TMP102/12345678",
      partNumber: "TMP102-ND",
      price: 0.85,
      quantity: 1,
      leadTimeDays: 0,
      inStock: true,
      rating: 4.8,
      lastUpdated: new Date().toISOString(),
    },
    {
      name: "Mouser",
      url: "https://www.mouser.com/ProductDetail/TI/TMP102",
      partNumber: "TMP102",
      price: 0.82,
      quantity: 1,
      leadTimeDays: 0,
      inStock: true,
      rating: 4.7,
      lastUpdated: new Date().toISOString(),
    },
  ],
};

export default function BOMSupplierManagement({
  parts,
  onSupplierSelect,
}: BOMSupplierManagementProps) {
  const [selectedPart, setSelectedPart] = useState<string | null>(null);
  const [sortBy, setSortBy] = useState<"price" | "leadTime" | "rating">("price");

  const partsWithSuppliers = useMemo(() => {
    return parts.map((part) => {
      const suppliers = MOCK_SUPPLIERS[part.mpn] || [];
      const bestPrice = suppliers.length > 0
        ? Math.min(...suppliers.map((s) => s.price))
        : normalizePrice(part.price);
      const currentPrice = normalizePrice(part.price);
      const savings = currentPrice > 0 ? currentPrice - bestPrice : 0;
      const savingsPercent = currentPrice > 0 ? (savings / currentPrice) * 100 : 0;

      return {
        part,
        suppliers: suppliers.sort((a, b) => {
          if (sortBy === "price") return a.price - b.price;
          if (sortBy === "leadTime") return a.leadTimeDays - b.leadTimeDays;
          return b.rating - a.rating;
        }),
        bestPrice,
        savings,
        savingsPercent,
        hasMultipleSuppliers: suppliers.length > 1,
      };
    });
  }, [parts, sortBy]);

  const totalPotentialSavings = useMemo(() => {
    return partsWithSuppliers.reduce((sum, item) => {
      return sum + item.savings * normalizeQuantity(item.part.quantity);
    }, 0);
  }, [partsWithSuppliers]);

  const partsNeedingSupplier = useMemo(() => {
    return parts.filter((part) => !MOCK_SUPPLIERS[part.mpn] || MOCK_SUPPLIERS[part.mpn].length === 0);
  }, [parts]);

  return (
    <div className="space-y-4">
      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Total Potential Savings</span>
            <TrendingDown className="w-5 h-5 text-green-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            ${totalPotentialSavings.toFixed(2)}
          </div>
          <div className="text-xs text-neutral-blue mt-1">
            By selecting best prices
          </div>
        </Card>

        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Parts with Suppliers</span>
            <ShoppingCart className="w-5 h-5 text-blue-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {partsWithSuppliers.filter((p) => p.suppliers.length > 0).length}
          </div>
          <div className="text-xs text-neutral-blue mt-1">
            of {parts.length} total parts
          </div>
        </Card>

        <Card className="p-4 bg-dark-surface border-dark-border">
          <div className="flex items-center justify-between mb-2">
            <span className="text-sm text-neutral-blue">Needs Supplier Data</span>
            <AlertTriangle className="w-5 h-5 text-yellow-400" />
          </div>
          <div className="text-2xl font-bold text-white">
            {partsNeedingSupplier.length}
          </div>
          <div className="text-xs text-neutral-blue mt-1">
            Parts missing supplier info
          </div>
        </Card>
      </div>

      {/* Supplier Comparison Table */}
      <Card className="p-4 bg-dark-surface border-dark-border">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <ShoppingCart className="w-5 h-5 text-neon-teal" />
            <h3 className="text-lg font-semibold text-white">Supplier Comparison</h3>
          </div>
          <div className="flex items-center gap-2">
            <label className="text-sm text-neutral-blue">Sort by:</label>
            <select
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value as any)}
              className="px-3 py-2 bg-dark-bg border border-dark-border rounded text-white text-sm focus:outline-none focus:border-neon-teal"
            >
              <option value="price">Price</option>
              <option value="leadTime">Lead Time</option>
              <option value="rating">Rating</option>
            </select>
          </div>
        </div>

        <div className="space-y-4">
          {partsWithSuppliers.map((item) => (
            <div
              key={item.part.componentId}
              className="border border-dark-border rounded-lg p-4 bg-dark-bg"
            >
              <div className="flex items-center justify-between mb-3">
                <div>
                  <div className="text-sm font-medium text-white">
                    {item.part.mpn}
                  </div>
                  <div className="text-xs text-neutral-blue">
                    {item.part.manufacturer} • Qty: {item.part.quantity || 1}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {item.savings > 0 && (
                    <Badge variant="default" className="bg-green-500/20 text-green-400">
                      Save ${item.savings.toFixed(2)} ({item.savingsPercent.toFixed(1)}%)
                    </Badge>
                  )}
                  {item.hasMultipleSuppliers && (
                    <Badge variant="outline" className="text-xs">
                      {item.suppliers.length} suppliers
                    </Badge>
                  )}
                </div>
              </div>

              {item.suppliers.length > 0 ? (
                <div className="space-y-2">
                  {item.suppliers.map((supplier, idx) => (
                    <div
                      key={idx}
                      className={`flex items-center justify-between p-3 rounded border ${
                        idx === 0 && item.savings > 0
                          ? "border-green-500/50 bg-green-500/10"
                          : "border-dark-border bg-zinc-900/30"
                      }`}
                    >
                      <div className="flex items-center gap-3 flex-1">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-sm font-medium text-white">
                              {supplier.name}
                            </span>
                            {idx === 0 && item.savings > 0 && (
                              <Badge variant="default" className="bg-green-500/20 text-green-400 text-xs">
                                Best Price
                              </Badge>
                            )}
                            {supplier.inStock ? (
                              <Badge variant="default" className="bg-green-500/20 text-green-400 text-xs">
                                <CheckCircle2 className="w-3 h-3 mr-1" />
                                In Stock
                              </Badge>
                            ) : (
                              <Badge variant="destructive" className="text-xs">
                                Out of Stock
                              </Badge>
                            )}
                          </div>
                          <div className="text-xs text-neutral-blue">
                            Part #: {supplier.partNumber}
                          </div>
                        </div>
                        <div className="flex items-center gap-4">
                          <div className="text-right">
                            <div className="text-sm font-semibold text-white">
                              ${supplier.price.toFixed(2)}
                            </div>
                            <div className="text-xs text-neutral-blue">
                              MOQ: {supplier.quantity}
                            </div>
                          </div>
                          <div className="text-right">
                            <div className="text-xs text-neutral-blue flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {supplier.leadTimeDays}d
                            </div>
                            <div className="text-xs text-neutral-blue flex items-center gap-1">
                              <Package className="w-3 h-3" />
                              {supplier.rating.toFixed(1)}★
                            </div>
                          </div>
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              onSupplierSelect?.(item.part.mpn, supplier);
                              window.open(supplier.url, "_blank");
                            }}
                            className="text-xs"
                          >
                            <ExternalLink className="w-3 h-3 mr-1" />
                            View
                          </Button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-3 bg-yellow-500/10 border border-yellow-500/50 rounded text-sm text-yellow-400">
                  <AlertTriangle className="w-4 h-4 inline mr-2" />
                  No supplier data available. Add supplier information to compare prices.
                </div>
              )}
            </div>
          ))}
        </div>
      </Card>
    </div>
  );
}

