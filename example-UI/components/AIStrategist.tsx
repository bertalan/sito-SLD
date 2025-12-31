import React, { useState } from 'react';
import { generateCreativeStrategy } from '../services/geminiService';
import { LoadingState } from '../types';
import { Sparkles, Loader2 } from 'lucide-react';

export const AIStrategist: React.FC = () => {
  const [prompt, setPrompt] = useState('');
  const [result, setResult] = useState('');
  const [status, setStatus] = useState<LoadingState>(LoadingState.IDLE);

  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    setStatus(LoadingState.LOADING);
    try {
      const strategy = await generateCreativeStrategy(prompt);
      setResult(strategy);
      setStatus(LoadingState.SUCCESS);
    } catch (error) {
      setResult("System Offline. Please try again later.");
      setStatus(LoadingState.ERROR);
    }
  };

  return (
    <section id="ai-strategy" className="py-24 bg-brand-silver border-y border-brand-gray/20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16">
          
          <div>
            <div className="flex items-center space-x-2 mb-6 text-brand-accent">
              <Sparkles size={20} />
              <span className="text-xs uppercase tracking-widest font-bold">AI Strategist Alpha</span>
            </div>
            <h2 className="text-4xl md:text-5xl font-bold tracking-tighter text-brand-black mb-6">
              ACCELERATE <br/> YOUR VISION.
            </h2>
            <p className="text-brand-gray text-lg mb-8 max-w-md">
              Use our proprietary Gemini-powered engine to generate an instant strategic outline for your next digital product.
            </p>
            
            <form onSubmit={handleGenerate} className="space-y-4">
              <textarea
                value={prompt}
                onChange={(e) => setPrompt(e.target.value)}
                placeholder="Describe your project (e.g., A minimalist e-commerce site for luxury watches targeting Gen Z)..."
                className="w-full bg-brand-white border border-brand-gray/30 p-4 text-brand-black placeholder-brand-gray/50 focus:outline-none focus:border-brand-accent transition-colors h-32 resize-none shadow-sm"
              />
              <button 
                type="submit" 
                disabled={status === LoadingState.LOADING || !prompt}
                className="bg-brand-black text-white px-8 py-4 font-bold tracking-wide uppercase hover:bg-brand-accent transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center w-full md:w-auto"
              >
                {status === LoadingState.LOADING ? (
                  <>
                    <Loader2 className="animate-spin mr-2" /> Processing
                  </>
                ) : (
                  'Generate Brief'
                )}
              </button>
            </form>
          </div>

          <div className="relative">
            {/* Dark Console for Contrast in Light Theme */}
            <div className="h-full w-full bg-brand-dark border border-brand-black p-8 min-h-[400px] shadow-2xl">
              <div className="flex justify-between items-center mb-6 border-b border-gray-800 pb-4">
                 <span className="text-xs uppercase tracking-widest text-gray-500">Output Console</span>
                 <div className="flex space-x-2">
                   <div className="w-2 h-2 rounded-full bg-brand-accent"></div>
                   <div className="w-2 h-2 rounded-full bg-gray-600"></div>
                   <div className="w-2 h-2 rounded-full bg-gray-600"></div>
                 </div>
              </div>
              
              <div className="font-mono text-sm leading-relaxed whitespace-pre-wrap text-gray-300">
                {status === LoadingState.IDLE && (
                  <span className="opacity-50 text-gray-500">// Waiting for input stream...</span>
                )}
                {status === LoadingState.LOADING && (
                  <span className="animate-pulse text-brand-accent">// Analyzing parameters...<br/>// Consultating Gemini Flash Model...</span>
                )}
                {status === LoadingState.SUCCESS && (
                  <span className="text-white">{result}</span>
                )}
                {status === LoadingState.ERROR && (
                   <span className="text-brand-accent">{result}</span>
                )}
              </div>
            </div>
            
            {/* Decorative background element */}
            <div className="absolute -z-10 top-4 left-4 w-full h-full border border-brand-gray/30 opacity-50 bg-white"></div>
          </div>

        </div>
      </div>
    </section>
  );
};