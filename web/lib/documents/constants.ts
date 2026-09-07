export const INDIA_REGIONS = [
  "Andhra Pradesh",
  "Arunachal Pradesh",
  "Assam",
  "Bihar",
  "Chhattisgarh",
  "Goa",
  "Gujarat",
  "Haryana",
  "Himachal Pradesh",
  "Jharkhand",
  "Karnataka",
  "Kerala",
  "Madhya Pradesh",
  "Maharashtra",
  "Manipur",
  "Meghalaya",
  "Mizoram",
  "Nagaland",
  "Odisha",
  "Punjab",
  "Rajasthan",
  "Sikkim",
  "Tamil Nadu",
  "Telangana",
  "Tripura",
  "Uttar Pradesh",
  "Uttarakhand",
  "West Bengal",
  "Andaman and Nicobar Islands",
  "Chandigarh",
  "Dadra and Nagar Haveli and Daman and Diu",
  "Delhi",
  "Jammu and Kashmir",
  "Ladakh",
  "Lakshadweep",
  "Puducherry",
] as const;

export const PARTY_TYPE_OPTIONS = [
  { value: "individual", label: "Individual" },
  { value: "company", label: "Company / body corporate" },
  { value: "firm", label: "Partnership / LLP / firm" },
  { value: "other", label: "Other legal person" },
];

export const DISPUTE_OPTIONS = [
  { value: "courts", label: "Courts at the chosen seat" },
  { value: "arbitration", label: "Arbitration, then courts for enforcement" },
];

export const DISCLAIMER =
  "This is an AI-generated draft — not an official legal filing and not legal advice. It is not valid merely because ChatLaw produced it. Laws vary by jurisdiction. Review every clause, complete placeholders, and obtain professional legal review before signing or filing.";

export const STATUS_LABELS = {
  draft: "Draft",
  review: "Review",
  final: "Final",
} as const;

export const DOCUMENT_CATEGORIES = [
  { value: "agreement", label: "Agreements & Contracts" },
  { value: "deed", label: "Deeds & Property" },
  { value: "complaint", label: "Complaints & Petitions" },
  { value: "notice", label: "Legal Notices" },
  { value: "affidavit", label: "Affidavits & Declarations" },
  { value: "application", label: "Statutory Applications" },
] as const;
