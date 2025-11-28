/**
 * Part Data Normalization Utilities
 * Ensures part data is always in the correct format to prevent runtime errors
 */

import type { PartObject } from "../../shared/services/types";

/**
 * Normalize price to always be a number
 * Handles cases where price might be a dict (from cost_estimate) or other types
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
    // Try common keys
    const value = price.value || price.cost || price.price || price.unit;
    if (value !== undefined) {
      const num = typeof value === "number" ? value : parseFloat(String(value));
      return isNaN(num) ? 0.0 : num;
    }
    // If no valid key, return 0
    return 0.0;
  }
  
  // Try to parse as string
  if (typeof price === "string") {
    // Remove currency symbols and whitespace
    const cleaned = price.replace(/[$,\s]/g, "").trim();
    const num = parseFloat(cleaned);
    return isNaN(num) ? 0.0 : num;
  }
  
  // Unknown type, return 0
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
  // Ensure price is always a number
  const normalizedPrice = normalizePrice(part.price);
  
  // Ensure quantity is always a number
  const normalizedQuantity = normalizeQuantity(part.quantity);
  
  return {
    ...part,
    price: normalizedPrice,
    quantity: normalizedQuantity,
    // Ensure componentId exists
    componentId: part.componentId || part.id || `part_${Date.now()}`,
  };
}

/**
 * Normalize an array of PartObjects
 */
export function normalizePartObjects(parts: any[]): PartObject[] {
  return parts.map(normalizePartObject);
}

