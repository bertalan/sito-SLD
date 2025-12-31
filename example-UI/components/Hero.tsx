import React from 'react';

export const Hero: React.FC = () => {
  return (
    <section className="relative min-h-screen flex items-center pt-20 bg-brand-white overflow-hidden border-b border-brand-gray/20">
      {/* Subtle Gradient Background */}
      <div className="absolute inset-0 z-0 opacity-50 bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-brand-silver via-brand-white to-brand-white pointer-events-none"></div>
      
      <div className="max-w-7xl mx-auto px-6 w-full relative z-10">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-12">
          
          <div className="lg:col-span-8">
            <h1 className="text-6xl md:text-8xl lg:text-9xl font-bold tracking-tighter text-brand-black leading-[0.9] mb-8">
              LEGAL <br/>
              PRECISION <br/>
              <span className="text-brand-accent">DESIGNED.</span>
            </h1>
          </div>

          <div className="lg:col-span-4 flex flex-col justify-end pb-4">
            <p className="text-lg md:text-xl text-brand-gray leading-relaxed mb-8 max-w-md">
              A strategic digital agency combining legal rigour with brutalist aesthetics. 
              We build authoritative web experiences.
            </p>
            
            <div className="flex flex-col space-y-4">
              <div className="h-[1px] w-full bg-brand-black"></div>
              <div className="flex justify-between text-sm text-brand-black uppercase tracking-widest">
                <span>EST. 2024</span>
                <span>Milano</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
};