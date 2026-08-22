export type LegalDomain =
  | "Criminal" | "Civil" | "Property" | "Family" | "Employment"
  | "Consumer" | "Cybercrime" | "Contract" | "Commercial" | "Tax"
  | "Intellectual Property" | "Motor Vehicle" | "Constitutional"
  | "Administrative" | "Immigration" | "Other";

export type ResourceType = "court" | "advocate";

export interface LocationInput {
  city?: string;
  state?: string;
  country?: string;
  latitude?: number;
  longitude?: number;
}

export interface CaseIntelligence {
  case_category: string;
  legal_domain: LegalDomain;
  sub_category: string | null;
  issue_summary: string;
  relevant_legal_topics: string[];
  jurisdiction: string | null;
  location: LocationInput | null;
  suggested_forum_types: string[];
  urgency: "routine" | "potentially_urgent";
  required_documents: string[];
  confidence: "low" | "medium" | "high";
  limitations: string[];
}

export interface SourceMetadata {
  source_url: string | null;
  source_type: string;
  verification_status: "verified" | "unverified" | "unavailable";
  retrieved_at: string | null;
}

export interface ResourceResult extends SourceMetadata {
  id: string;
  name: string;
  type: ResourceType;
  practice_areas?: string[];
  court_type?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  latitude?: number | null;
  longitude?: number | null;
  phone?: string | null;
  profile_url?: string | null;
  official_url?: string | null;
  distance_km?: number | null;
}

export interface ProviderSearchInput {
  location: LocationInput;
  jurisdiction?: string | null;
  caseCategory?: string | null;
  practiceArea?: string | null;
  radiusKm: number;
}

export interface ResourceProvider {
  search(input: ProviderSearchInput): Promise<ResourceResult[]>;
}