def detect_query_type(messages):

    latest = messages[-1].content.lower()

    
    # Comparison Queries
    

    comparison_words = [
        "compare",
        "difference",
        "vs",
        "versus"
    ]

    if any(word in latest for word in comparison_words):
        return "comparison"

    
    # Refinement Queries
    

    refinement_words = [
        "add",
        "remove",
        "drop",
        "replace",
        "include",
        "exclude"
    ]

    if any(word in latest for word in refinement_words):
        return "refinement"

    
    # Off-topic Queries
    

    off_topic_words = [
        "salary",
        "legal",
        "compliance",
        "tax",
        "contract"
    ]

    if any(word in latest for word in off_topic_words):
        return "off_topic"

    
    # Clarification Logic
    

    vague_queries = [
        "need assessment",
        "need test",
        "looking for assessment",
        "hiring",
        "need solution"
    ]

    # only clarify if query is VERY short/vague
    if (
        len(latest.split()) < 5
        or latest.strip() in vague_queries
    ):
        return "clarification"

    
    # Default Recommendation
    

    return "recommendation"