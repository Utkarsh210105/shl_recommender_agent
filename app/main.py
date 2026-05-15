from fastapi import FastAPI

from app.models import ChatRequest
from app.retriever import search_assessments
from app.logic import detect_query_type
from app.llm import generate_response
from app.prompts import SYSTEM_PROMPT

app = FastAPI()


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/chat")
def chat(req: ChatRequest):

    query_type = detect_query_type(req.messages)

    latest_user_message = req.messages[-1].content

    latest_lower = latest_user_message.lower()

    
    # Unsupported Skill Handling
    

    unsupported_skills = [
        "rust",
        "elixir",
        "haskell",
        "cobol"
    ]

    if any(skill in latest_lower for skill in unsupported_skills):

        return {
            "reply": (
                "SHL's catalog does not currently include a dedicated assessment "
                "for this technology. However, I can recommend adjacent assessments "
                "covering systems programming, networking, coding, or cognitive ability. "
                "Would you like me to build a shortlist?"
            ),
            "recommendations": None,
            "end_of_conversation": False
        }

    conversation_history = "\n".join(
        [f"{m.role}: {m.content}" for m in req.messages]
    )

    
    # Clarification Handling
    

    if query_type == "clarification":

        return {
            "reply": "Could you share more details about the role, seniority, or skills needed?",
            "recommendations": [],
            "end_of_conversation": False
        }

    
    # Off-topic Refusal
    

    if query_type == "off_topic":

        return {
            "reply": "I can only help with SHL assessment recommendations and comparisons.",
            "recommendations": [],
            "end_of_conversation": False
        }

    
    # Comparison Mode
    

    if query_type == "comparison":

        retrieved = search_assessments(latest_user_message, top_k=10)

        context = ""

        for item in retrieved:

            context += f"""
            Name: {item.get('name', '')}

            Description:
            {item.get('description', '')}

            Test Types:
            {", ".join(item.get('keys', []))}

            URL:
            {item.get('link', '')}
            """

        prompt = f"""
        {SYSTEM_PROMPT}

        Conversation History:
        {conversation_history}

        Retrieved Catalog:
        {context}

        Compare the relevant assessments clearly.

        Explain:
        - primary purpose
        - differences
        - ideal usage scenarios

        Use ONLY retrieved catalog information.
        Keep response concise and professional.
        """

        reply = generate_response(prompt)

        recommendations = []

        seen = set()

        for item in retrieved:

            name = item.get("name", "")

            if name not in seen:

                recommendations.append({
                    "name": name,
                    "url": item.get("link", ""),
                    "test_type": ", ".join(item.get("keys", [])[:2])
                })

                seen.add(name)

            if len(recommendations) >= 5:
                break

        return {
            "reply": reply,
            "recommendations": recommendations,
            "end_of_conversation": False
        }

    
    # Refinement Detection
    

    refinement_keywords = [
        "add",
        "remove",
        "drop",
        "replace",
        "include",
        "exclude"
    ]

    is_refinement = any(
        word in latest_lower for word in refinement_keywords
    )

    if is_refinement:

        combined_query = conversation_history

    else:

        combined_query = latest_user_message

    
    # Retrieval
    

    retrieved = search_assessments(combined_query)

    
    # Build Catalog Context
    

    context = ""

    for item in retrieved:

        context += f"""
        Name: {item.get('name', '')}

        Description:
        {item.get('description', '')}

        Job Levels:
        {", ".join(item.get('job_levels', []))}

        Test Types:
        {", ".join(item.get('keys', []))}

        Duration:
        {item.get('duration', '')}

        Languages:
        {", ".join(item.get('languages', []))}

        URL:
        {item.get('link', '')}
        """

    
    # Prompt
    

    prompt = f"""
    {SYSTEM_PROMPT}

    Conversation History:
    {conversation_history}

    Retrieved Catalog:
    {context}

    Instructions:
    - Recommend the most relevant SHL assessments.
    - Use ONLY retrieved catalog entries.
    - Avoid hallucinations.
    - Avoid duplicate recommendations.
    - Prefer technical assessments for technical roles.
    - Prefer safety/vigilance tests for industrial roles.
    - Prefer cognitive tests for graduate/senior hiring.
    - Explain recommendations briefly.
    - Keep response concise and professional.
    """

    
    # Generate Reply
    

    reply = generate_response(prompt)

    
    # Remove Duplicates
    

    filtered = []

    seen = set()

    for item in retrieved:

        name = item.get("name", "")

        if name not in seen:

            filtered.append(item)

            seen.add(name)

    
    # Diverse Selection
    

    selected = []

    used_types = set()

    for item in filtered:

        item_types = tuple(item.get("keys", []))

        if item_types not in used_types:

            selected.append(item)

            used_types.add(item_types)

        if len(selected) >= 5:
            break

    
    # Fallback Fill
    

    if len(selected) < 5:

        for item in filtered:

            if item not in selected:

                selected.append(item)

            if len(selected) >= 5:
                break

    
    # Recommendation Payload
    

    recommendations = []

    for item in selected:

        recommendations.append({
            "name": item.get("name", ""),
            "url": item.get("link", ""),
            "test_type": ", ".join(item.get("keys", [])[:2])
        })

    
    # Conversation Completion
    

    end_words = [
        "perfect",
        "confirmed",
        "that works",
        "looks good",
        "finalize",
        "final list",
        "lock it in",
        "thanks"
    ]

    end_of_conversation = any(
        word in latest_lower for word in end_words
    )

    
    # Final Response
    

    return {
        "reply": reply,
        "recommendations": recommendations,
        "end_of_conversation": end_of_conversation
    }