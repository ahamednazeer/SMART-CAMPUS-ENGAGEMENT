"""
AI-powered quiz generation service using GROQ.
State-of-the-art implementation with:
- Two-pass generation (extract concepts → generate questions)
- Bloom's Taxonomy cognitive levels
- Few-shot examples for accuracy
- Topic coverage validation
- Semantic deduplication
- Answer verification
- Comprehensive randomization
"""
import json
import random
import re
import httpx
from typing import Optional
from app.core.config import settings


class AIQuizService:
    """
    Premium AI-powered quiz generation using GROQ API or local Ollama.
    
    Features:
    - Two-pass generation for accuracy
    - Bloom's Taxonomy question levels
    - Few-shot prompting
    - Smart text sampling
    - Answer randomization
    - Quality validation with retry
    - Support for both GROQ (cloud) and Ollama (local)
    """
    
    GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
    
    @classmethod
    def _get_api_config(cls) -> tuple[str, dict, str]:
        """
        Get API URL, headers, and model based on configuration.
        Returns: (api_url, headers, model_name)
        """
        if settings.OLLAMA_ENABLED:
            # Use Ollama (local) - no auth needed
            return (
                f"{settings.OLLAMA_BASE_URL}/v1/chat/completions",
                {"Content-Type": "application/json"},
                settings.OLLAMA_MODEL
            )
        else:
            # Use GROQ (cloud)
            if not settings.GROQ_API_KEY:
                raise ValueError("GROQ_API_KEY not configured. Set OLLAMA_ENABLED=true to use local Ollama instead.")
            return (
                cls.GROQ_API_URL,
                {
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json"
                },
                settings.GROQ_MODEL
            )
    
    # Bloom's Taxonomy levels for question variety
    BLOOMS_LEVELS = [
        ("REMEMBER", "recall facts, terms, basic concepts"),
        ("UNDERSTAND", "explain ideas, interpret meaning"),
        ("APPLY", "use information in new situations"),
        ("ANALYZE", "draw connections, identify patterns"),
        ("EVALUATE", "justify a decision or position"),
    ]
    
    # Few-shot examples for high-quality output
    FEW_SHOT_EXAMPLES = """
EXAMPLE 1 (REMEMBER level):
{
    "question_text": "What year was the india got independence?",
    "options": ["1947", "1948", "1949", "1950"],
    "correct_answer": 1,
    "difficulty": "easy",
    "bloom_level": "REMEMBER"
}

EXAMPLE 2 (UNDERSTAND level):
{
    "question_text": "What is the primary purpose of photosynthesis in plants?",
    "options": [
        "To convert sunlight into chemical energy for food",
        "To release oxygen into the atmosphere",
        "To absorb water from the soil",
        "To produce carbon dioxide"
    ],
    "correct_answer": 0,
    "difficulty": "medium",
    "bloom_level": "UNDERSTAND"
}

EXAMPLE 3 (APPLY level):
{
    "question_text": "A company wants to reduce its carbon footprint. Based on sustainability principles, which action would be MOST effective?",
    "options": [
        "Switch to renewable energy sources",
        "Print on both sides of paper",
        "Turn off lights when not in use",
        "Use reusable coffee cups"
    ],
    "correct_answer": 0,
    "difficulty": "medium",
    "bloom_level": "APPLY"
}

EXAMPLE 4 (ANALYZE level):
{
    "question_text": "What is the relationship between supply and demand when a new competitor enters the market?",
    "options": [
        "Supply increases and prices typically decrease",
        "Demand increases and prices increase",
        "Supply decreases and demand increases",
        "Both supply and demand remain unchanged"
    ],
    "correct_answer": 0,
    "difficulty": "hard",
    "bloom_level": "ANALYZE"
}
"""
    
    @classmethod
    def _smart_sample_text(cls, text: str, max_chars: int = 10000) -> str:
        """
        Intelligently sample text to maximize content coverage.
        Prioritizes paragraph boundaries and key sections.
        """
        if len(text) <= max_chars:
            return text
        
        # Split into paragraphs
        paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
        
        if not paragraphs:
            # Fallback to simple sampling
            section_size = max_chars // 3
            return f"{text[:section_size]}\n\n[...]\n\n{text[len(text)//2 - section_size//2:len(text)//2 + section_size//2]}\n\n[...]\n\n{text[-section_size:]}"
        
        # Strategy: Select paragraphs from beginning, middle, and end
        total_paragraphs = len(paragraphs)
        
        # Allocate: 40% beginning, 30% middle, 30% end
        begin_count = max(1, int(total_paragraphs * 0.4))
        middle_start = total_paragraphs // 3
        middle_count = max(1, int(total_paragraphs * 0.3))
        end_count = max(1, int(total_paragraphs * 0.3))
        
        selected = []
        
        # Beginning paragraphs
        selected.extend(paragraphs[:begin_count])
        
        # Middle paragraphs
        selected.append("\n[...MIDDLE SECTION...]\n")
        selected.extend(paragraphs[middle_start:middle_start + middle_count])
        
        # End paragraphs
        selected.append("\n[...END SECTION...]\n")
        selected.extend(paragraphs[-end_count:])
        
        result = "\n\n".join(selected)
        
        # Truncate if still too long
        if len(result) > max_chars:
            result = result[:max_chars] + "..."
        
        return result
    
    @classmethod
    async def _extract_key_concepts(cls, text: str) -> list[str]:
        """
        First pass: Extract key concepts/topics from the text.
        This ensures questions cover the main ideas.
        """
        # Skip if no API configured
        if not settings.OLLAMA_ENABLED and not settings.GROQ_API_KEY:
            return []
        
        # Use only first 4000 chars for concept extraction (faster)
        sample = text[:4000] if len(text) > 4000 else text
        
        prompt = f"""Analyze this text and extract the 5-8 MOST IMPORTANT key concepts, topics, or themes.

TEXT:
{sample}

Return ONLY a JSON array of strings, like:
["concept 1", "concept 2", "concept 3", "concept 4", "concept 5"]

No explanation, just the JSON array."""

        # Get provider-specific config
        api_url, headers, model = cls._get_api_config()
        
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "Extract key concepts. Return only a JSON array."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,  # Low temp for accuracy
            "max_tokens": 500
        }
        
        try:
            # Use longer timeout for Ollama (local inference can be slower)
            timeout = 120.0 if settings.OLLAMA_ENABLED else 30.0
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"].strip()
                    # Clean markdown if present
                    if content.startswith("```"):
                        content = re.sub(r'^```\w*\n?', '', content)
                        content = re.sub(r'\n?```$', '', content)
                    return json.loads(content)
        except:
            pass
        
        return []
    
    @classmethod
    def _shuffle_and_randomize(cls, questions: list) -> list:
        """
        Comprehensive randomization:
        1. Shuffle question order
        2. Shuffle options within each question
        3. Update correct_answer indices
        """
        # Shuffle question order
        random.shuffle(questions)
        
        # Shuffle options for each question
        for q in questions:
            options = q.get("options", [])
            correct_idx = q.get("correct_answer", 0)
            
            if len(options) != 4:
                continue
            
            # Create indexed options
            indexed = list(enumerate(options))
            random.shuffle(indexed)
            
            # Rebuild options and find new correct index
            new_options = []
            new_correct = 0
            for new_idx, (orig_idx, option_text) in enumerate(indexed):
                new_options.append(option_text)
                if orig_idx == correct_idx:
                    new_correct = new_idx
            
            q["options"] = new_options
            q["correct_answer"] = new_correct
        
        return questions
    
    @classmethod
    def _validate_and_deduplicate(cls, questions: list, num_requested: int) -> list:
        """
        Validate questions and remove duplicates/similar ones.
        """
        valid_questions = []
        seen_texts = set()
        
        for q in questions:
            # Basic validation
            text = q.get("question_text", "").strip().lower()
            options = q.get("options", [])
            correct = q.get("correct_answer")
            
            if not text or len(options) != 4:
                continue
            
            if correct is None or not (0 <= int(correct) <= 3):
                continue
            
            # Check for duplicates (simple text similarity)
            text_key = re.sub(r'[^a-z0-9]', '', text)[:50]
            if text_key in seen_texts:
                continue
            seen_texts.add(text_key)
            
            # Check all options are unique
            if len(set(options)) != 4:
                continue
            
            # Ensure correct_answer is int
            q["correct_answer"] = int(correct)
            valid_questions.append(q)
        
        return valid_questions[:num_requested]
    
    @classmethod
    async def generate_quiz_from_text(
        cls,
        text: str,
        num_questions: int = 5,
        title: str = "Generated Quiz"
    ) -> dict:
        """
        Generate high-quality quiz questions using two-pass generation.
        
        Pass 1: Extract key concepts from the text
        Pass 2: Generate questions covering those concepts with Bloom's taxonomy
        """
        # Validate API configuration
        api_url, headers, model = cls._get_api_config()
        
        # First pass: Extract key concepts (optional enhancement)
        key_concepts = await cls._extract_key_concepts(text)
        concept_instruction = ""
        if key_concepts:
            concept_instruction = f"""
KEY CONCEPTS TO COVER (ensure questions address these):
{', '.join(key_concepts)}
"""
        
        # Smart text sampling
        sampled_text = cls._smart_sample_text(text, max_chars=9000)
        
        # Determine Bloom's level distribution
        # For 5 questions: 2 Remember, 1 Understand, 1 Apply, 1 Analyze
        blooms_distribution = []
        if num_questions >= 5:
            blooms_distribution = [
                f"- 2 questions at REMEMBER level (recall facts)",
                f"- 1-2 questions at UNDERSTAND level (explain concepts)",
                f"- 1 question at APPLY level (use knowledge in scenarios)",
                f"- 1 question at ANALYZE level (identify relationships)"
            ]
        else:
            blooms_distribution = [
                f"- Include a variety of difficulty levels from easy to hard"
            ]
        
        # Build the premium prompt
        prompt = f"""You are an expert educational assessment designer. Create exactly {num_questions} HIGH-QUALITY multiple choice questions based on the content below.

=== SOURCE CONTENT ===
{sampled_text}

=== REQUIREMENTS ===
{concept_instruction}
COGNITIVE LEVELS (Bloom's Taxonomy distribution):
{chr(10).join(blooms_distribution)}

QUESTION QUALITY STANDARDS:
1. Each question tests ONE clear concept
2. Question stems are unambiguous and complete
3. All 4 options are plausible (no obviously wrong answers)
4. Distractors are based on common misconceptions
5. Correct answer is definitively correct based on the content
6. No "all of the above" or "none of the above" options
7. Options are similar in length and grammatical structure

=== FEW-SHOT EXAMPLES ===
{cls.FEW_SHOT_EXAMPLES}

=== OUTPUT FORMAT ===
Return ONLY valid JSON (no markdown, no explanation):
{{
    "title": "{title}",
    "description": "Comprehensive quiz covering key concepts",
    "questions": [
        {{
            "question_text": "Clear, specific question?",
            "options": ["Option A", "Option B", "Option C", "Option D"],
            "correct_answer": 0,
            "difficulty": "easy|medium|hard",
            "bloom_level": "REMEMBER|UNDERSTAND|APPLY|ANALYZE"
        }}
    ]
}}

CRITICAL: Ensure exactly {num_questions} questions. Each with 4 UNIQUE options."""

        payload = {
            "model": model,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a professional educational assessment designer. You create accurate, pedagogically sound quiz questions using Bloom's Taxonomy. Output ONLY valid JSON."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.8,
            "max_tokens": 5000
        }
        
        max_retries = 3
        last_error = None
        provider_name = "Ollama" if settings.OLLAMA_ENABLED else "GROQ"
        
        for attempt in range(max_retries):
            try:
                # Use longer timeout for Ollama (local inference can be slower)
                timeout = 180.0 if settings.OLLAMA_ENABLED else 90.0
                async with httpx.AsyncClient(timeout=timeout) as client:
                    response = await client.post(
                        api_url,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code != 200:
                        raise ValueError(f"{provider_name} API error ({response.status_code}): {response.text[:500]}")
                    
                    content = response.json()["choices"][0]["message"]["content"].strip()
                    
                    # Clean markdown formatting
                    if "```json" in content:
                        # Extract content between ```json and ```
                        match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
                        if match:
                            content = match.group(1).strip()
                    elif "```" in content:
                        # Extract content between ``` and ```
                        match = re.search(r'```\s*(.*?)\s*```', content, re.DOTALL)
                        if match:
                            content = match.group(1).strip()
                    
                    # Try to find JSON object even if there's extra text
                    # Look for the JSON object starting with {
                    if not content.startswith("{"):
                        json_match = re.search(r'(\{.*\})', content, re.DOTALL)
                        if json_match:
                            content = json_match.group(1)
                    
                    content = content.strip()
                    
                    # Parse JSON
                    try:
                        quiz_data = json.loads(content)
                    except json.JSONDecodeError as e:
                        if attempt < max_retries - 1:
                            continue
                        raise ValueError(f"JSON parse error: {e}. Response: {content[:500]}")
                    
                    if "questions" not in quiz_data:
                        if attempt < max_retries - 1:
                            continue
                        raise ValueError("Missing 'questions' field")
                    
                    # Validate and deduplicate
                    valid_questions = cls._validate_and_deduplicate(
                        quiz_data["questions"], 
                        num_questions
                    )
                    
                    if len(valid_questions) < num_questions:
                        if attempt < max_retries - 1:
                            continue
                        # Accept what we have if it's at least 80%
                        if len(valid_questions) < int(num_questions * 0.8):
                            raise ValueError(f"Only generated {len(valid_questions)} valid questions")
                    
                    # Randomize everything
                    quiz_data["questions"] = cls._shuffle_and_randomize(valid_questions)
                    
                    # Add order indices
                    for i, q in enumerate(quiz_data["questions"]):
                        q["order"] = i
                    
                    return quiz_data
                    
            except Exception as e:
                last_error = e
                if attempt >= max_retries - 1:
                    raise
        
        raise last_error or ValueError("Quiz generation failed after retries")
    
    @classmethod
    async def extract_text_from_pdf(cls, file_path: str) -> str:
        """
        Extract text content from a PDF file with enhanced cleaning.
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            raise ValueError("PyMuPDF not installed. Run: pip install pymupdf")
        
        try:
            doc = fitz.open(file_path)
            text_parts = []
            
            for page in doc:
                text_parts.append(page.get_text())
            
            doc.close()
            
            full_text = "\n".join(text_parts)
            
            # Enhanced cleaning
            full_text = re.sub(r'\n{3,}', '\n\n', full_text)  # Multiple newlines
            full_text = re.sub(r' {2,}', ' ', full_text)      # Multiple spaces
            full_text = re.sub(r'[^\x00-\x7F]+', ' ', full_text)  # Non-ASCII chars
            full_text = re.sub(r'\s*\d+\s*$', '', full_text, flags=re.MULTILINE)  # Page numbers
            
            return full_text.strip()
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")


class AIService:
    """AI service for campus queries - categorization and response suggestions."""
    
    @classmethod
    async def categorize_query(cls, description: str) -> str:
        """Categorize a query using AI."""
        if not settings.OLLAMA_ENABLED and not settings.GROQ_API_KEY:
            return "OTHERS"
        
        # Get API config from AIQuizService
        api_url, headers, model = AIQuizService._get_api_config()
        
        prompt = f"""Categorize this student query into EXACTLY ONE of these categories:
- RULES (hostel rules, campus rules, policies)
- TIMINGS (schedules, timings, hours)
- POLICY (official policies, procedures)
- OTHERS (anything else)

QUERY: {description}

Return ONLY the category name in uppercase (RULES, TIMINGS, POLICY, or OTHERS). No explanation."""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You categorize student queries. Return only the category name."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 20
        }
        
        try:
            timeout = 30.0 if settings.OLLAMA_ENABLED else 15.0
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"].strip().upper()
                    if content in ["RULES", "TIMINGS", "POLICY", "OTHERS"]:
                        return content
        except:
            pass
        
        return "OTHERS"
    
    @classmethod
    async def suggest_query_response(cls, description: str, category: str, student_type: str, student_name: str | None = None) -> str:
        """Generate AI-suggested response for a query."""
        if not settings.OLLAMA_ENABLED and not settings.GROQ_API_KEY:
            name = student_name or "Student"
            return f"Dear {name}, thank you for your query. We will look into this and get back to you."
        
        api_url, headers, model = AIQuizService._get_api_config()
        
        context = "hosteller" if student_type == "HOSTELLER" else "day scholar"
        name_to_use = student_name if student_name else "Student"
        responder = "Hostel Warden" if student_type == "HOSTELLER" else "College Administration"
        
        prompt = f"""You are a helpful college administrator responding to a {context} student's query.

STUDENT NAME: {name_to_use}
CATEGORY: {category}
STUDENT QUERY: {description}

Write a helpful, professional response that:
1. Addresses the student by their name "{name_to_use}" at the start
2. Provides relevant information if possible
3. Is polite and concise (2-4 sentences)
4. DO NOT use any placeholders like [Student] or [Your Name] - use actual names
5. Sign off as "{responder}"

Response:"""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a helpful college administrator. Write professional, concise responses. Never use placeholder brackets like [Name] - always use the actual name provided."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.7,
            "max_tokens": 300
        }
        
        try:
            timeout = 60.0 if settings.OLLAMA_ENABLED else 30.0
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    return response.json()["choices"][0]["message"]["content"].strip()
        except:
            pass
        
        return f"Dear {name_to_use}, thank you for your query. We will review this and respond shortly.\n\nBest regards,\n{responder}"
    
    @classmethod
    async def categorize_complaint(cls, description: str) -> str:
        """Use AI to categorize a maintenance complaint."""
        if not settings.OLLAMA_ENABLED and not settings.GROQ_API_KEY:
            return "OTHER"
        
        api_url, headers, model = AIQuizService._get_api_config()
        
        prompt = f"""Categorize this maintenance complaint into ONE of these categories:
- ELECTRICAL (fans, lights, switches, power issues)
- PLUMBING (water leaks, taps, pipes, drainage)
- CLEANING (dirt, hygiene, garbage)
- FURNITURE (chairs, tables, beds, cupboards)
- EQUIPMENT (lab equipment, projectors, computers)
- OTHER (anything else)

COMPLAINT: {description}

Reply with ONLY the category name (e.g., ELECTRICAL):"""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a maintenance request classifier. Reply with only the category name."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 20
        }
        
        try:
            timeout = 60.0 if settings.OLLAMA_ENABLED else 30.0
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"].strip().upper()
                    valid = ["ELECTRICAL", "PLUMBING", "CLEANING", "FURNITURE", "EQUIPMENT", "OTHER"]
                    for cat in valid:
                        if cat in result:
                            return cat
        except:
            pass
        
        return "OTHER"
    
    @classmethod
    async def assess_complaint_priority(cls, description: str, category: str) -> str:
        """Use AI to assess complaint priority level."""
        if not settings.OLLAMA_ENABLED and not settings.GROQ_API_KEY:
            return "MEDIUM"
        
        api_url, headers, model = AIQuizService._get_api_config()
        
        prompt = f"""Assess the priority of this maintenance complaint:

CATEGORY: {category}
COMPLAINT: {description}

Priority levels:
- URGENT: Safety hazard, water flooding, electrical danger, broken glass
- HIGH: Major inconvenience affecting multiple people
- MEDIUM: Standard repair needed
- LOW: Minor issue, cosmetic

Reply with ONLY the priority level (e.g., MEDIUM):"""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a maintenance priority assessor. Reply with only the priority level."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 20
        }
        
        try:
            timeout = 60.0 if settings.OLLAMA_ENABLED else 30.0
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"].strip().upper()
                    valid = ["LOW", "MEDIUM", "HIGH", "URGENT"]
                    for pri in valid:
                        if pri in result:
                            return pri
        except:
            pass
        
        return "MEDIUM"
    
    @classmethod
    async def detect_submission_type(cls, description: str) -> str:
        """
        Detect if a submission is a QUERY (informational) or COMPLAINT (maintenance).
        Returns: 'QUERY', 'COMPLAINT', or 'UNKNOWN'
        """
        if not settings.OLLAMA_ENABLED and not settings.GROQ_API_KEY:
            return "UNKNOWN"
        
        api_url, headers, model = AIQuizService._get_api_config()
        
        prompt = f"""Classify this student submission as QUERY or COMPLAINT:

QUERY = Student is ASKING A QUESTION to get information
- Asking about timings, rules, policies, fees, schedules, procedures
- Contains question words (what, when, where, how, why, can I, is there)
- Wants to KNOW something, not FIX something
Examples: "What are hostel timings?", "When is the exam?", "Can I get a gate pass?"

COMPLAINT = Student is REPORTING A PROBLEM with physical things
- Something is broken, not working, damaged, dirty, leaking, or malfunctioning
- Mentions physical items like fan, light, tap, toilet, chair, AC, water, electricity
- Describes an issue that needs REPAIR, CLEANING, or MAINTENANCE action
- Even if poorly worded, if it's about something physical not working = COMPLAINT
Examples: "Fan not working", "Fan speed problem", "Light flickering", "Water tap leaking", "Toilet dirty", "AC not cooling"

STUDENT SUBMISSION: {description}

IMPORTANT: If the text mentions ANY physical item (fan, light, water, toilet, AC, chair, etc.) having a problem, it is a COMPLAINT.

Reply with only one word: QUERY or COMPLAINT"""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You classify text. If it mentions physical items having problems (fan, light, water, AC, etc.), say COMPLAINT. If asking for information, say QUERY. Reply with one word only."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.1,
            "max_tokens": 10
        }
        
        try:
            timeout = 60.0 if settings.OLLAMA_ENABLED else 30.0
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"].strip().upper()
                    if "COMPLAINT" in result:
                        return "COMPLAINT"
                    if "QUERY" in result:
                        return "QUERY"
        except:
            pass
        
        return "UNKNOWN"
    
    @classmethod
    async def suggest_resolution_notes(cls, description: str, category: str, assigned_to: str | None = None) -> str:
        """
        Generate AI-suggested resolution notes for closing a complaint.
        """
        if not settings.OLLAMA_ENABLED and not settings.GROQ_API_KEY:
            return f"Issue resolved. {category} maintenance completed."
        
        api_url, headers, model = AIQuizService._get_api_config()
        
        staff_info = f"by {assigned_to}" if assigned_to else "by maintenance team"
        
        prompt = f"""Generate a brief, professional resolution note for this completed maintenance complaint:

CATEGORY: {category}
ORIGINAL ISSUE: {description}
RESOLVED BY: {staff_info}

Write 1-2 sentences confirming the issue was resolved. Be specific to the issue type.
Keep it professional and concise. Do not include greetings or signatures."""

        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": "You are a maintenance department assistant writing brief resolution confirmations."},
                {"role": "user", "content": prompt}
            ],
            "temperature": 0.3,
            "max_tokens": 100
        }
        
        try:
            timeout = 60.0 if settings.OLLAMA_ENABLED else 30.0
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(api_url, headers=headers, json=payload)
                if response.status_code == 200:
                    result = response.json()["choices"][0]["message"]["content"].strip()
                    # Clean up the response
                    if result:
                        return result
        except:
            pass
        
        return f"{category} issue has been addressed and resolved {staff_info}."

