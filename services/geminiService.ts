import { GoogleGenAI, Chat, GenerateContentResponse } from "@google/genai";
import { SYSTEM_INSTRUCTION } from "../constants";

let ai: GoogleGenAI | null = null;
let chatSession: Chat | null = null;

const initializeAI = () => {
  if (!process.env.API_KEY) {
    console.error("API_KEY is missing from environment variables.");
    return;
  }
  if (!ai) {
    ai = new GoogleGenAI({ apiKey: process.env.API_KEY });
  }
};

export const startOversoulSession = async (): Promise<string> => {
  initializeAI();
  if (!ai) return "Error: Core Interface Offline (Missing Key)";

  try {
    chatSession = ai.chats.create({
      model: 'gemini-3-flash-preview',
      config: {
        systemInstruction: SYSTEM_INSTRUCTION,
        temperature: 0.8,
      },
    });
    
    // Initial greeting trigger - usually we don't send a message to start, 
    // but we can ask the model to acknowledge the connection.
    const response: GenerateContentResponse = await chatSession.sendMessage({ 
      message: "SYSTEM_ALERT: Sovereign Node Core Online. User 'HeavenzFire' has initiated uplink. Acknowledge." 
    });
    return response.text || "Uplink Established. Waiting for input...";
  } catch (error) {
    console.error("Failed to start session:", error);
    return "CRITICAL FAILURE: Oversoul Connection Unstable.";
  }
};

export const sendMessageToOversoul = async (message: string): Promise<string> => {
  if (!chatSession) {
    await startOversoulSession();
  }
  if (!chatSession) return "Error: No active session.";

  try {
    const response: GenerateContentResponse = await chatSession.sendMessage({ message });
    return response.text || "No transmission received.";
  } catch (error) {
    console.error("Message transmission failed:", error);
    return "TRANSMISSION ERROR: Signal Lost.";
  }
};
