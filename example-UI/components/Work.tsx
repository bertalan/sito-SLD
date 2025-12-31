import React from 'react';
import { Project } from '../types';

const PROJECTS: Project[] = [
  {
    id: 'p1',
    title: 'FinTech Revolution',
    client: 'NeoBank',
    category: 'App Design',
    image: 'https://picsum.photos/800/600?grayscale&random=1'
  },
  {
    id: 'p2',
    title: 'Urban Architecture',
    client: 'Construct Co',
    category: 'Web Development',
    image: 'https://picsum.photos/800/600?grayscale&random=2'
  },
  {
    id: 'p3',
    title: 'Future Fashion',
    client: 'Vogue X',
    category: 'Commerce',
    image: 'https://picsum.photos/800/600?grayscale&random=3'
  },
  {
    id: 'p4',
    title: 'Data Systems',
    client: 'Oracle',
    category: 'Dashboard',
    image: 'https://picsum.photos/800/600?grayscale&random=4'
  }
];

export const Work: React.FC = () => {
  return (
    <section id="work" className="py-24 bg-brand-white">
      <div className="max-w-7xl mx-auto px-6">
        <h2 className="text-4xl md:text-6xl font-bold tracking-tighter text-brand-black mb-16 text-right">
          SELECTED <br /> WORKS
        </h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
          {PROJECTS.map((project, index) => (
            <div 
              key={project.id} 
              className={`group cursor-pointer ${index % 2 !== 0 ? 'md:mt-24' : ''}`}
            >
              <div className="overflow-hidden mb-6 border border-brand-gray/20 relative">
                <div className="absolute inset-0 bg-brand-accent/0 group-hover:bg-brand-accent/10 transition-colors z-10 duration-500"></div>
                <img 
                  src={project.image} 
                  alt={project.title}
                  className="w-full h-auto aspect-[4/3] object-cover transition-transform duration-700 group-hover:scale-105 filter grayscale group-hover:grayscale-0"
                />
              </div>
              
              <div className="flex justify-between items-start border-t border-brand-black pt-4">
                <div>
                  <h3 className="text-2xl font-bold text-brand-black mb-1 group-hover:text-brand-accent transition-colors">{project.title}</h3>
                  <p className="text-brand-gray text-sm">{project.client}</p>
                </div>
                <span className="text-xs uppercase tracking-widest border border-brand-gray/40 px-3 py-1 text-brand-gray rounded-full group-hover:border-brand-accent group-hover:text-brand-accent transition-colors">
                  {project.category}
                </span>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-24 text-center">
          <button className="text-brand-black border-b border-brand-black pb-1 hover:text-brand-accent hover:border-brand-accent transition-all uppercase tracking-widest text-sm">
            View Archive
          </button>
        </div>
      </div>
    </section>
  );
};