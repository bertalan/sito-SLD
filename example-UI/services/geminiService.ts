import { GoogleGenAI } from "@google/genai";

const apiKey = process.env.API_KEY || '';
const ai = new GoogleGenAI({ apiKey });

export const generateCreativeStrategy = async (clientBrief: string): Promise<string> => {
  if (!apiKey) {
    throw new Error("API Key is missing. Please configure process.env.API_KEY.");
  }

  try {
    const response = await ai.models.generateContent({
      model: 'gemini-3-flash-preview',
      contents: `Act as a senior digital strategist for a high-end design agency. 
      Create a brief, high-impact strategic outline for the following client request. 
      Focus on "Objective", "Approach", and "Key Deliverables". 
      Keep it punchy, professional, and abstract (max 150 words).
      
      Client Request: ${clientBrief}`,
      config: {
        systemInstruction: "You are a minimalist, brutalist design strategist. You speak in concise, high-value terms.",
        temperature: 0.7,
      }
    });

    return response.text || "Unable to generate strategy at this time.";
  } catch (error) {
    console.error("Gemini API Error:", error);
    throw new Error("Failed to generate creative strategy.");
  }
};