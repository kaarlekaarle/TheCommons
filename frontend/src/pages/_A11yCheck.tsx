import React from 'react';
import Button from '../components/ui/Button';
import Badge from '../components/ui/Badge';

export default function A11yCheck() {
  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-h1 font-bold text-neutral-900 mb-8">Accessibility Design Check</h1>
      
      {/* Typography */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Typography</h2>
        <div className="space-y-4">
          <div>
            <h1 className="text-h1 font-bold text-neutral-900">Heading 1 (H1)</h1>
            <p className="text-sm text-neutral-600">clamp(2.25rem, 2.2vw + 1.5rem, 3rem) - line-height: 1.2</p>
          </div>
          <div>
            <h2 className="text-h2 font-bold text-neutral-900">Heading 2 (H2)</h2>
            <p className="text-sm text-neutral-600">2rem - line-height: 1.3</p>
          </div>
          <div>
            <h3 className="text-h3 font-bold text-neutral-900">Heading 3 (H3)</h3>
            <p className="text-sm text-neutral-600">1.5rem - line-height: 1.4</p>
          </div>
          <div>
            <p className="text-base text-neutral-700">Body text (16px) - line-height: 1.75</p>
            <p className="text-sm text-neutral-600">Small text (14px) - line-height: 1.45</p>
          </div>
        </div>
      </section>

      {/* Colors */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Color Palette</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="space-y-2">
            <div className="h-16 bg-neutral-900 rounded-lg"></div>
            <p className="text-sm font-medium">neutral-900</p>
            <p className="text-xs text-neutral-600">#0f172a</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 bg-neutral-800 rounded-lg"></div>
            <p className="text-sm font-medium">neutral-800</p>
            <p className="text-xs text-neutral-600">#1f2937</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 bg-neutral-700 rounded-lg"></div>
            <p className="text-sm font-medium">neutral-700</p>
            <p className="text-xs text-neutral-600">#334155</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 bg-neutral-600 rounded-lg"></div>
            <p className="text-sm font-medium">neutral-600</p>
            <p className="text-xs text-neutral-600">#475569</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 bg-primary-600 rounded-lg"></div>
            <p className="text-sm font-medium">primary-600</p>
            <p className="text-xs text-neutral-600">#1f54b5</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 bg-primary-700 rounded-lg"></div>
            <p className="text-sm font-medium">primary-700</p>
            <p className="text-xs text-neutral-600">#183f87</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 bg-success-600 rounded-lg"></div>
            <p className="text-sm font-medium">success-600</p>
            <p className="text-xs text-neutral-600">#148343</p>
          </div>
          <div className="space-y-2">
            <div className="h-16 bg-success-700 rounded-lg"></div>
            <p className="text-sm font-medium">success-700</p>
            <p className="text-xs text-neutral-600">#0f6336</p>
          </div>
        </div>
      </section>

      {/* Buttons */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Buttons</h2>
        <div className="space-y-4">
          <div className="flex flex-wrap gap-4">
            <Button variant="primary">Primary Button</Button>
            <Button variant="secondary">Secondary Button</Button>
            <Button variant="ghost">Ghost Button</Button>
            <Button variant="success">Success Button</Button>
          </div>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary" size="sm">Small</Button>
            <Button variant="primary" size="md">Medium</Button>
            <Button variant="primary" size="lg">Large</Button>
          </div>
        </div>
      </section>

      {/* Badges */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Badges</h2>
        <div className="flex flex-wrap gap-4">
          <Badge variant="principle">Principle (Level A)</Badge>
          <Badge variant="action">Action (Level B)</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="danger">Danger</Badge>
        </div>
      </section>

      {/* Cards */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Cards</h2>
        <div className="grid md:grid-cols-2 gap-6">
          <div className="card">
            <h3 className="text-h3 font-bold text-neutral-900 mb-2">Card Title</h3>
            <p className="text-base text-neutral-700 mb-4">
              This is a sample card with the new USWDS-inspired design. It uses the .card utility class.
            </p>
            <div className="flex items-center text-sm text-neutral-600">
              <span>Sample metadata</span>
            </div>
          </div>
          <div className="card border-l-4 border-l-primary-500 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-primary-500 to-primary-600"></div>
            <h3 className="text-h3 font-bold text-neutral-900 mb-2">Principle Card (Level A)</h3>
            <p className="text-base text-neutral-700 mb-4">
              This card shows how Level A (Principles) cards should look with subtle blue accents - left border and top header bar.
            </p>
          </div>
          <div className="card border-l-4 border-l-success-500 relative overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-success-500 to-success-600"></div>
            <h3 className="text-h3 font-bold text-neutral-900 mb-2">Action Card (Level B)</h3>
            <p className="text-base text-neutral-700 mb-4">
              This card shows how Level B (Actions) cards should look with subtle green accents - left border and top header bar.
            </p>
          </div>
        </div>
      </section>

      {/* Links */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Links</h2>
        <div className="space-y-2">
          <p className="text-base text-neutral-700">
            This is a paragraph with a <a href="#" className="focus-ring">sample link</a> that uses the new link styles.
          </p>
          <p className="text-base text-neutral-700">
            Another paragraph with a <a href="#" className="focus-ring">second link</a> for testing.
          </p>
        </div>
      </section>

      {/* Focus States */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Focus States</h2>
        <div className="space-y-4">
          <p className="text-base text-neutral-700">
            Tab through these elements to see focus states:
          </p>
          <div className="flex flex-wrap gap-4">
            <Button variant="primary" className="focus-ring">Focusable Button</Button>
            <a href="#" className="focus-ring inline-block px-4 py-2 bg-white border border-neutral-300 rounded-lg text-neutral-900">Focusable Link</a>
            <input 
              type="text" 
              placeholder="Focusable input" 
              className="px-3 py-2 border border-neutral-300 rounded-lg focus-ring"
            />
          </div>
        </div>
      </section>

      {/* Contrast Check */}
      <section className="mb-12">
        <h2 className="text-h2 font-bold text-neutral-900 mb-6">Contrast Check</h2>
        <div className="space-y-4">
          <div className="p-4 bg-white border border-neutral-200 rounded-lg">
            <h3 className="text-h3 font-bold text-neutral-900 mb-2">White Background</h3>
            <p className="text-base text-neutral-700 mb-2">Body text on white should be neutral-700</p>
            <p className="text-sm text-neutral-600">Small text on white should be neutral-600</p>
          </div>
          <div className="p-4 bg-neutral-50 border border-neutral-200 rounded-lg">
            <h3 className="text-h3 font-bold text-neutral-900 mb-2">Light Background</h3>
            <p className="text-base text-neutral-700 mb-2">Body text on light bg should be neutral-700</p>
            <p className="text-sm text-neutral-600">Small text on light bg should be neutral-600</p>
          </div>
        </div>
      </section>
    </div>
  );
}
