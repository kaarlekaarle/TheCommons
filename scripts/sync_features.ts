#!/usr/bin/env tsx

import { readFileSync, writeFileSync } from 'fs';
import { join } from 'path';

interface Feature {
  title: string;
  description: string;
  icon?: string;
}

interface GeneratedManifest {
  generatedAt: string;
  items: Feature[];
}

function validateFeature(feature: any): feature is Feature {
  if (typeof feature !== 'object' || feature === null) {
    return false;
  }
  
  if (typeof feature.title !== 'string' || feature.title.trim() === '') {
    return false;
  }
  
  if (typeof feature.description !== 'string' || feature.description.trim() === '') {
    return false;
  }
  
  if (feature.icon !== undefined && typeof feature.icon !== 'string') {
    return false;
  }
  
  return true;
}

function validateFeatures(features: any): features is Feature[] {
  if (!Array.isArray(features)) {
    return false;
  }
  
  return features.every(validateFeature);
}

async function syncFeatures() {
  try {
    // Determine if we're running from repo root or frontend directory
    const currentDir = process.cwd();
    const isInFrontend = currentDir.endsWith('frontend');
    
    const repoRoot = isInFrontend ? join(currentDir, '..') : currentDir;
    const featuresPath = join(repoRoot, 'frontend', 'src', 'config', 'features.ts');
    const outputPath = join(repoRoot, 'frontend', 'src', 'config', 'features.generated.json');
    
    console.log('📖 Reading features from:', featuresPath);
    
    // Read the features.ts file
    const featuresContent = readFileSync(featuresPath, 'utf-8');
    
    // Extract the features array using regex
    const exportMatch = featuresContent.match(/export const features = (\[[\s\S]*?\]);/);
    if (!exportMatch) {
      throw new Error('Could not find "export const features = [...]" in features.ts');
    }
    
    // Evaluate the features array safely
    const featuresCode = exportMatch[1];
    const features = eval(featuresCode);
    
    console.log('🔍 Validating features structure...');
    
    if (!validateFeatures(features)) {
      throw new Error('Features validation failed. Each feature must have title (string) and description (string), with optional icon (string).');
    }
    
    console.log(`✅ Found ${features.length} valid features`);
    
    // Create the manifest
    const manifest: GeneratedManifest = {
      generatedAt: new Date().toISOString(),
      items: features
    };
    
    // Write the JSON file
    const jsonContent = JSON.stringify(manifest, null, 2) + '\n';
    writeFileSync(outputPath, jsonContent, 'utf-8');
    
    console.log('📝 Generated manifest at:', outputPath);
    console.log('✨ Features sync completed successfully');
    
  } catch (error) {
    console.error('❌ Features sync failed:', error instanceof Error ? error.message : error);
    process.exit(1);
  }
}

// Run the sync
syncFeatures();
