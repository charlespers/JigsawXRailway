/**
 * BOM Supplier Links Component
 * Quick access to supplier pages for parts
 */

import React from "react";
import { Card } from "../../../shared/components/ui/card";
import { Button } from "../../../shared/components/ui/button";
import { Badge } from "../../../shared/components/ui/badge";
import { ExternalLink, ShoppingCart, Package } from "lucide-react";
import type { PartObject } from "../../../shared/services/types";

interface BOMSupplierLinksProps {
  parts: PartObject[];
}

interface Supplier {
  name: string;
  url: (mpn: string, manufacturer: string) => string;
  icon?: React.ReactNode;
}

const suppliers: Supplier[] = [
  {
    name: "DigiKey",
    url: (mpn) => `https://www.digikey.com/en/products/result?keywords=${encodeURIComponent(mpn)}`,
    icon: <ShoppingCart className="w-4 h-4" />,
  },
  {
    name: "Mouser",
    url: (mpn) => `https://www.mouser.com/Search/Refine?Keyword=${encodeURIComponent(mpn)}`,
    icon: <Package className="w-4 h-4" />,
  },
  {
    name: "Octopart",
    url: (mpn, manufacturer) => 
      `https://octopart.com/search?q=${encodeURIComponent(`${manufacturer} ${mpn}`)}`,
    icon: <ExternalLink className="w-4 h-4" />,
  },
];

export default function BOMSupplierLinks({ parts }: BOMSupplierLinksProps) {
  return (
    <Card className="bg-dark-surface border-dark-border p-4">
      <div className="flex items-center gap-2 mb-4">
        <ShoppingCart className="w-5 h-5 text-neutral-blue" />
        <h3 className="text-lg font-semibold text-white">Supplier Links</h3>
        <Badge variant="outline" className="text-xs">
          {parts.length} part(s)
        </Badge>
      </div>

      <div className="space-y-3">
        {parts.map((part) => (
          <div
            key={part.componentId}
            className="p-3 bg-dark-bg rounded border border-dark-border"
          >
            <div className="flex items-start justify-between mb-2">
              <div className="flex-1">
                <div className="text-sm font-medium text-white font-mono mb-1">
                  {part.mpn}
                </div>
                <div className="text-xs text-neutral-blue">
                  {part.manufacturer}
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2 flex-wrap">
              {suppliers.map((supplier) => (
                <Button
                  key={supplier.name}
                  size="sm"
                  variant="outline"
                  onClick={() => {
                    const url = supplier.url(part.mpn, part.manufacturer);
                    window.open(url, "_blank");
                  }}
                  className="text-xs h-7"
                >
                  {supplier.icon}
                  <span className="ml-1">{supplier.name}</span>
                </Button>
              ))}
            </div>
          </div>
        ))}
      </div>
    </Card>
  );
}

