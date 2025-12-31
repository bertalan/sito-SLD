import React from 'react';

export const Footer: React.FC = () => {
  return (
    <footer id="contact" className="bg-brand-dark pt-24 pb-12 border-t border-brand-gray/20">
      <div className="max-w-7xl mx-auto px-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-12 mb-24">
          <div>
            <h2 className="text-5xl md:text-7xl font-bold tracking-tighter text-white mb-8">
              LET'S <br/> TALK.
            </h2>
            <a 
              href="mailto:hello@eloq.agency" 
              className="text-xl md:text-2xl text-brand-gray hover:text-brand-accent transition-colors border-b border-brand-gray/30 pb-1"
            >
              hello@eloq.agency
            </a>
          </div>
          
          <div className="flex flex-col justify-end">
             <form className="space-y-6 max-w-md ml-auto w-full">
                <div>
                   <label className="block text-xs uppercase tracking-widest text-brand-gray mb-2">Email</label>
                   <input type="email" className="w-full bg-transparent border-b border-brand-gray/30 py-2 text-white focus:outline-none focus:border-brand-accent transition-colors" />
                </div>
                <div>
                   <label className="block text-xs uppercase tracking-widest text-brand-gray mb-2">Message</label>
                   <textarea rows={3} className="w-full bg-transparent border-b border-brand-gray/30 py-2 text-white focus:outline-none focus:border-brand-accent transition-colors"></textarea>
                </div>
                <button type="button" className="text-white text-sm font-bold uppercase tracking-widest text-left hover:text-brand-accent transition-colors pt-4">
                  Send Message &rarr;
                </button>
             </form>
          </div>
        </div>

        <div className="flex flex-col md:flex-row justify-between items-center text-xs text-brand-gray uppercase tracking-widest pt-12 border-t border-brand-gray/10">
          <div className="mb-4 md:mb-0">
            &copy; {new Date().getFullYear()} ELOQ Agency.
          </div>
          <div className="flex space-x-6">
            <a href="#" className="hover:text-white transition-colors">Instagram</a>
            <a href="#" className="hover:text-white transition-colors">Twitter</a>
            <a href="#" className="hover:text-white transition-colors">LinkedIn</a>
          </div>
        </div>
      </div>
    </footer>
  );
};