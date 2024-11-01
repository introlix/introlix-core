from keybert import KeyBERT

# Initialize KeyBERT
kw_model = KeyBERT()

# Sample list of titles
titles = [
    "Make Your Own AI Image Generator with Bria 2.3 Model",
    "GPT-4 vs. Llama 3.1 – Which Model is Better?",
    "How to learn coding faster?",
    "Keyword Extraction Methods from Documents in NLP"
]

# Predefined list of good tags
good_tags = {'ai', 'ml', 'machine learning', 'nlp', 'data science', 'generator', 'coding', 'model'}

# Generate and display tags for each title
for title in titles:
    keywords = kw_model.extract_keywords(title, top_n=5, stop_words='english')
    # Extract only the keywords (the first element of each tuple)
    tags = [keyword[0] for keyword in keywords if keyword[0] in good_tags]
    
    # If no tags are found, you might consider adding a default tag
    if not tags:
        tags = ['general']  # Example of a fallback tag

    # Format tags for display
    formatted_tags = ', '.join(tags)
    
    print(f"Title: {title}")
    print(f"Tags: [{formatted_tags}]\n")
