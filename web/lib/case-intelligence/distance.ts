import type { ResourceResult, LocationInput } from "./types";

const EARTH_RADIUS_KM = 6371;

export function haversineDistanceKm(a: LocationInput, b: LocationInput): number | null {
  if (![a.latitude, a.longitude, b.latitude, b.longitude].every((value) => typeof value === "number" && Number.isFinite(value))) return null;
  const toRadians = (value: number) => value * Math.PI / 180;
  const latDelta = toRadians((b.latitude as number) - (a.latitude as number));
  const lonDelta = toRadians((b.longitude as number) - (a.longitude as number));
  const lat1 = toRadians(a.latitude as number);
  const lat2 = toRadians(b.latitude as number);
  const h = Math.sin(latDelta / 2) ** 2 + Math.cos(lat1) * Math.cos(lat2) * Math.sin(lonDelta / 2) ** 2;
  return EARTH_RADIUS_KM * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

export function sortAndFilterByDistance(results: ResourceResult[], location: LocationInput, radiusKm: number): ResourceResult[] {
  return results
    .map((result) => ({ ...result, distance_km: haversineDistanceKm(location, { latitude: result.latitude ?? undefined, longitude: result.longitude ?? undefined }) }))
    .filter((result) => result.distance_km === null || result.distance_km <= radiusKm)
    .sort((a, b) => (a.distance_km ?? Number.POSITIVE_INFINITY) - (b.distance_km ?? Number.POSITIVE_INFINITY));
}