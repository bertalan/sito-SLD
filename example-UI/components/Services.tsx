import React from 'react';
import { Service } from '../types';
import { ArrowUpRight } from 'lucide-react';

const SERVICES: Service[] = [
  {
    id: '1',
    title: 'Strategy',
    description: 'Market analysis, brand positioning, and digital transformation roadmaps.',
    tags: ['Research', 'Audit', 'Planning']
  },
  {
    id: '2',
    title: 'Design',
    description: 'UI/UX design, design systems, and interaction models that define brands.',
    tags: ['UI/UX', 'Motion', 'Systems']
  },
  {
    id: '3',
    title: 'Development',
    description: 'Full-stack engineering, headless CMS implementation, and performance tuning.',
    tags: ['React', 'Wagtail', 'Python']
  }
];

export const Services: React.FC = () => {
  return (
    <section id="services" className="py-24 bg-brand-white border-b border-brand-gray/20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="flex flex-col md:flex-row justify-between items-end mb-16">
          <h2 className="text-4xl md:text-6xl font-bold tracking-tighter text-brand-black">
            OUR <br /> EXPERTISE
          </h2>
          <span className="text-brand-gray uppercase tracking-widest text-sm mt-4 md:mt-0">
            Full Cycle Production
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-0 border-t border-l border-brand-gray/20">
          {SERVICES.map((service) => (
            <div 
              key={service.id} 
              className="group p-8 border-r border-b border-brand-gray/20 hover:bg-brand-silver transition-colors duration-300 relative min-h-[400px] flex flex-col justify-between"
            >
              <div className="absolute top-8 right-8 opacity-0 group-hover:opacity-100 transition-opacity">
                <ArrowUpRight className="text-brand-accent w-6 h-6" />
              </div>
              
              <div>
                <span className="text-xs text-brand-gray font-mono mb-4 block">0{service.id}</span>
                <h3 className="text-3xl font-bold text-brand-black mb-4 tracking-tight group-hover:text-brand-accent transition-colors">{service.title}</h3>
              </div>

              <div>
                <p className="text-brand-gray text-sm leading-relaxed mb-6">
                  {service.description}
                </p>
                <div className="flex flex-wrap gap-2">
                  {service.tags.map(tag => (
                    <span key={tag} className="text-xs border border-brand-gray/40 px-2 py-1 rounded-full text-brand-gray uppercase group-hover:border-brand-accent group-hover:text-brand-accent transition-colors">
                      {tag}
                    </span>
                  ))}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};