declare module "*.json" {
  const value: unknown;
  export default value;
}

interface Feature {
  title: string;
  description: string;
  icon?: string;
}

interface FeaturesManifest {
  generatedAt: string;
  items: Feature[];
}
