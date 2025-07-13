import os
from typing import List, Literal
from groq import AsyncGroq
from app.models import Note


async def generate_profile_insight(self, notes: List[Note]) -> str:
        """Generate profile insight from a list of recent notes."""
        
        system_prompt = """You are an expert data analyst specializing in personal productivity and behavior patterns. Your task is to analyze user notes and provide insights in a specific format.

Analyze the provided notes and give output in this EXACT format:
- Interests:
- Most Active Time:
- Recent Focus:
- Average Sentiment:
- Weekly Summary:
- Suggested Topics:

Guidelines:
1. Interests: List 3-5 main topics/themes based on tags and content
2. Most Active Time: Determine peak activity hours from timestamps
3. Recent Focus: Identify what the user has been concentrating on lately
4. Average Sentiment: Assess overall mood (positive/neutral/negative) with brief explanation
5. Weekly Summary: Provide a 2-3 sentence overview of the week's activities
6. Suggested Topics: Recommend 3-4 topics they might want to explore based on their patterns

Be concise, insightful, and specific. Use the exact format with dashes and colons."""

        # Format notes data for analysis
        notes_text = "Here are the notes:\n\n"
        for note in notes:
            notes_text += f"Title: {note.title or 'Untitled'}\n"
            notes_text += f"Tags: {', '.join(note.tags)}\n"
            notes_text += f"Content: {note.content}\n"
            notes_text += f"Created: {note.created_at.isoformat()}\n\n"
        
        user_prompt = notes_text + "\nPlease analyze these notes and provide profile insights in the specified format."
        
        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",
                temperature=0.7,
                top_p=0.9,
                max_tokens=2048,
                stream=False
            )
            
            if not response.choices or not response.choices[0].message:
                raise Exception("Empty response from Groq API")
            
            content = response.choices[0].message.content
            if not content:
                raise Exception("No content in Groq API response")
                
            return content.strip()
            
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")



class GroqService:
    def __init__(self, api_key: str):
        self.client = AsyncGroq(api_key=api_key)
    
    async def process_note(
        self, 
        note: Note, 
        command: Literal["summarize", "enlarge", "format"]
    ) -> str:
        """Process a note using Groq LLM API."""
        
        if command == "summarize":
            system_prompt = """You are an expert content summarizer. Your task is to:
1. Create a concise summary of the provided content
2. Keep the summary to 120 words or less
3. Maintain the key information and context
4. Write in clear, professional language
5. Return only the summary text, no additional formatting"""
            
            user_prompt = f"""Content: {note.content}
Tags: {', '.join(note.tags)}

Please provide a concise summary of this content."""
            
        elif command == "enlarge":
            system_prompt = """You are an expert content expander. Your task is to:
1. Start your response with the exact first sentence from the original content (do not modify it)
2. Expand the content to 800-1000 words
3. Include at least one ordered list (1. 2. 3.) or unordered list (- or *)
4. Add relevant details, examples, and explanations
5. Maintain the original topic and context
6. Write in an engaging, informative style
7. Return only the expanded content, no additional formatting"""
            
            user_prompt = f"""Content: {note.content}
Tags: {', '.join(note.tags)}

Please expand this content to 800-1000 words, starting with the exact first sentence unchanged."""
        
        elif command == "format":
            system_prompt = """You are an expert content formatter. Your task is to:
1. Take unformatted, poorly structured text and make it well-formatted
2. Organize content into clear paragraphs with proper sentence structure
3. Fix grammar, spelling, and punctuation errors
4. Improve readability while preserving the original meaning
5. Add appropriate structure with headings if needed
6. Include bullet points or numbered lists where appropriate to organize information
7. Ensure proper capitalization and spacing
8. Return only the formatted content, no additional commentary"""
            
            user_prompt = f"""Content: {note.content}
Tags: {', '.join(note.tags)}

Please format this content properly. Fix any grammar, spelling, punctuation issues and organize it into a well-structured, readable format."""
            
        elif command == "profile_insight":
            return await generate_profile_insight(self, [note])
        

        try:
            response = await self.client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                model="llama-3.1-8b-instant",  # Updated model name
                temperature=0.7,
                top_p=0.9,
                max_tokens=2048,
                stream=False
            )
            
            if not response.choices or not response.choices[0].message:
                raise Exception("Empty response from Groq API")
            
            content = response.choices[0].message.content
            if not content:
                raise Exception("No content in Groq API response")
                
            return content.strip()
            
        except Exception as e:
            raise Exception(f"Groq API error: {str(e)}")


def get_groq_service() -> GroqService:
    """Dependency to get Groq service instance."""
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is required")
    return GroqService(api_key=api_key)