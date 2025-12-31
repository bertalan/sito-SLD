import React from 'react';
import { HashRouter } from 'react-router-dom';
import { Navigation } from './components/Navigation';
import { Hero } from './components/Hero';
import { Services } from './components/Services';
import { Work } from './components/Work';
import { AIStrategist } from './components/AIStrategist';
import { Footer } from './components/Footer';

/**
 * Main App Component
 * 
 * Note: While this project is built in React/TypeScript, the data structure
 * and component hierarchy are designed to be easily hydrated by a JSON API 
 * from a Headless Wagtail CMS backend.
 */
function App() {
  return (
    <HashRouter>
      <div className="bg-brand-white min-h-screen flex flex-col font-sans selection:bg-brand-accent selection:text-white">
        <Navigation />
        
        <main className="flex-grow">
          <Hero />
          <Services />
          <Work />
          <AIStrategist />
        </main>
        
        <Footer />
      </div>
    </HashRouter>
  );
}

export default App;