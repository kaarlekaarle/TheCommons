export interface LevelAPreset {
  id: string;
  label: string;
}

export const LEVEL_A_PRESETS: readonly LevelAPreset[] = [
  { id: "transportation_safety", label: "Transportation Safety" },
  { id: "government_transparency", label: "Government Transparency" },
  { id: "environmental_policy", label: "Environmental Policy" },
  { id: "housing_development", label: "Housing & Development" },
  { id: "parks_recreation", label: "Parks & Recreation" },
  { id: "climate_sustainability", label: "Climate & Sustainability" },
  { id: "financial_management", label: "Financial Management" },
  { id: "technology_innovation", label: "Technology & Innovation" },
  { id: "arts_culture", label: "Arts & Culture" },
  { id: "food_security", label: "Food Security" },
  { id: "public_transit", label: "Public Transit" },
  { id: "public_health", label: "Public Health" },
  { id: "water_management", label: "Water Management" },
  { id: "waste_management", label: "Waste Management" },
  { id: "civic_engagement", label: "Civic Engagement" },
  { id: "labor_employment", label: "Labor & Employment" },
  { id: "public_safety", label: "Public Safety" },
  { id: "urban_forestry", label: "Urban Forestry" },
  { id: "heritage_conservation", label: "Heritage Conservation" }
] as const;

// Helper function to get labels as a simple string array for backward compatibility
export const LEVEL_A_CHOICES = LEVEL_A_PRESETS.map(preset => preset.label);

// Helper function to find a preset by label
export const findPresetByLabel = (label: string): LevelAPreset | undefined => {
  return LEVEL_A_PRESETS.find(preset => preset.label === label);
};

// Helper function to find a preset by id
export const findPresetById = (id: string): LevelAPreset | undefined => {
  return LEVEL_A_PRESETS.find(preset => preset.id === id);
};
