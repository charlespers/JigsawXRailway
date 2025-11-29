/**
 * Part Data Normalization Utilities
 * Ensures part data is always in the correct format to prevent runtime errors
 */

import type { PartObject } from "../services/types";

/**
 * Normalize price to always be a number
 * Handles cases where price might be a dict (from cost_estimate) or other types
 * Prioritizes cost_estimate.value format (standard in our JSON)
 */
export function normalizePrice(price: any): number {
  if (price === null || price === undefined) {
    return 0.0;
  }
  
  // Already a number
  if (typeof price === "number") {
    return isNaN(price) ? 0.0 : price;
  }
  
  // If it's a dict, try to extract value
  if (typeof price === "object" && price !== null) {
    // Try common keys - prioritize 'value' as it's standard in cost_estimate
    const value = price.value || price.unit || price.cost || price.price;
    if (value !== undefined) {
      const num = typeof value === "number" ? value : parseFloat(String(value));
      if (isNaN(num)) {
        console.warn(`Price normalization failed: invalid number from ${JSON.stringify(price)}`);
        return 0.0;
      }
      return num;
    }
    // If no valid key, log warning and return 0
    console.warn(`Price normalization failed: no valid key found in ${JSON.stringify(price)}`);
    return 0.0;
  }
  
  // Try to parse as string
  if (typeof price === "string") {
    // Remove currency symbols and whitespace
    const cleaned = price.replace(/[$,\s]/g, "").trim();
    const num = parseFloat(cleaned);
    return isNaN(num) ? 0.0 : num;
  }
  
  // Unknown type, log warning and return 0
  console.warn(`Price normalization failed: unknown type ${typeof price} for ${price}`);
  return 0.0;
}

/**
 * Normalize quantity to always be a positive integer
 */
export function normalizeQuantity(quantity: any): number {
  if (quantity === null || quantity === undefined) {
    return 1;
  }
  
  if (typeof quantity === "number") {
    return Math.max(1, Math.floor(quantity));
  }
  
  if (typeof quantity === "string") {
    const num = parseInt(quantity, 10);
    return isNaN(num) ? 1 : Math.max(1, num);
  }
  
  return 1;
}

/**
 * Normalize a PartObject to ensure all numeric fields are numbers
 * This prevents "dict * float" errors in the frontend
 */
export function normalizePartObject(part: any): PartObject {
  // Extract price from multiple possible locations
  let priceToNormalize = part.price;
  
  // Check cost_estimate object if price is not directly available
  if ((priceToNormalize === undefined || priceToNormalize === null || priceToNormalize === 0) && part.cost_estimate) {
    priceToNormalize = part.cost_estimate.value || part.cost_estimate.unit || part.cost_estimate.price;
  }
  
  // Also check partData if it exists (from MCP endpoint)
  if ((priceToNormalize === undefined || priceToNormalize === null || priceToNormalize === 0) && part.partData) {
    priceToNormalize = part.partData.price || part.partData.cost || 
                      (part.partData.cost_estimate?.value || part.partData.cost_estimate?.unit);
  }
  
  // Ensure price is always a number
  const normalizedPrice = normalizePrice(priceToNormalize);
  
  // Ensure quantity is always a number
  const normalizedQuantity = normalizeQuantity(part.quantity);
  
  return {
    ...part,
    price: normalizedPrice,
    quantity: normalizedQuantity,
    // Ensure componentId exists
    componentId: part.componentId || part.id || part.partData?.mpn || `part_${Date.now()}`,
  };
}

/**
 * Normalize an array of PartObjects
 */
export function normalizePartObjects(parts: any[]): PartObject[] {
  return parts.map(normalizePartObject);
}

