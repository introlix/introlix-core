from keybert import KeyBERT

# Initialize KeyBERT
kw_model = KeyBERT()

# Sample list of titles
titles = [
    "Make Your Own AI Image Generator with Bria 2.3 Model",
    "GPT-4 vs. Llama 3.1 – Which Model is Better?",
    "How to learn coding faster?",
    "Keyword Extraction Methods from Documents in NLP",
    "Best machine learning model for text generation"
]

# Predefined list of good tags
good_tags = {'ai', 'ml', 'machine-learning', 'text-generation', 'nlp', 'data-science', 'generator', 'coding', 'model'}

# Generate and display tags for each title
for title in titles:
    # Normalize the title to lowercase and replace spaces with hyphens for consistent matching
    normalized_title = title.lower().replace(' ', '-')

    # Check for tags in good_tags that appear in the normalized title
    tags = [tag for tag in good_tags if tag in normalized_title]
    
    # If no tags are found, you might consider adding a default tag
    if not tags:
        tags = ['general']  # Example of a fallback tag

    # Format tags for display
    formatted_tags = ', '.join(tags)
    
    print(f"Title: {title}")
    print(f"Tags: [{formatted_tags}]\n")
