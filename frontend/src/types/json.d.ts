declare module "*.json" {
  const value: any;
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
