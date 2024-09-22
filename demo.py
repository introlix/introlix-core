import time
import requests
import concurrent.futures

titles = [
    # World News
    "Global Summit Addresses Climate Change Crisis",
    "New Trade Agreement Signed Between EU and China",
    "Political Tensions Rise in the Middle East Amidst New Sanctions",
    "UN Releases Report on Global Poverty and Hunger",
    "World Leaders Gather to Discuss Pandemic Preparedness",
    "Protests Erupt Across Latin America Over Economic Inequality",
    "Major Earthquake Hits Indonesia, Thousands Affected",
    "Biden and Xi Meet to Discuss Future of US-China Relations",
    "Wildfires Continue to Ravage Australia, Displacing Thousands",
    "EU Faces New Challenges Amid Brexit Aftermath",

    # Sci/Tech
    "Breakthrough in Quantum Computing Brings Faster Processors",
    "NASA Plans to Launch Mars Rover Mission Next Month",
    "The Future of Space Tourism: Companies Race to the Stars",
    "New Advances in AI and Machine Learning Transform Healthcare",
    "Scientists Develop Renewable Energy Source from Ocean Waves",
    "How 5G Technology is Shaping the Future of Connectivity",
    "The Evolution of Virtual Reality in the Gaming Industry",
    "Tech Giants Collaborate to Build Smart Cities of the Future",
    "Exploring the Ethical Dilemmas of Genetic Engineering",
    "Scientists Unveil New Findings on Dark Matter",

    # Coding
    "Mastering Python for Web Development: Tips and Tricks",
    "10 Must-Know JavaScript Libraries for Developers",
    "How to Build a REST API Using Node.js and Express",
    "Understanding Data Structures and Algorithms in Java",
    "An Introduction to Functional Programming with Haskell",
    "Building Scalable Web Apps with Django and PostgreSQL",
    "Exploring the Latest Features of React 18",
    "Automating Tasks with Python: A Beginner's Guide",
    "Best Practices for Writing Clean and Maintainable Code",
    "Debugging Techniques Every Developer Should Know",

    # AI
    "AI-Powered Healthcare: Revolutionizing Diagnosis and Treatment",
    "The Role of Artificial Intelligence in Autonomous Vehicles",
    "Understanding the Ethical Concerns Surrounding AI Development",
    "How AI is Shaping the Future of Creative Industries",
    "Using AI to Predict Stock Market Trends",
    "AI in Education: Personalized Learning Through Machine Learning",
    "The Impact of AI on the Job Market: Threat or Opportunity?",
    "Exploring the Use of AI in Cybersecurity Threat Detection",
    "Can AI Solve the Climate Crisis? A Look at Emerging Technologies",
    "AI Chatbots: Enhancing Customer Experience and Business Efficiency",

    # ML
    "Machine Learning Algorithms Explained: A Beginner’s Guide",
    "Supervised vs. Unsupervised Learning: Key Differences",
    "How Machine Learning is Transforming Financial Services",
    "Implementing Neural Networks for Image Classification",
    "Using Machine Learning to Predict Customer Churn",
    "The Role of Feature Engineering in Machine Learning Models",
    "Exploring the Power of Deep Learning for Natural Language Processing",
    "How Reinforcement Learning is Advancing Robotics",
    "Evaluating Model Performance with Precision and Recall",
    "Understanding Transfer Learning and Its Applications",

    # Nature
    "Exploring the World's Most Endangered Species",
    "How Deforestation is Impacting Global Biodiversity",
    "The Role of Wetlands in Preserving Our Ecosystem",
    "Coral Reefs in Crisis: What Can Be Done to Save Them?",
    "The Impact of Climate Change on Arctic Wildlife",
    "How Bees and Other Pollinators are Essential to Agriculture",
    "Conservation Efforts to Protect the Amazon Rainforest",
    "The Importance of Sustainable Agriculture for Future Generations",
    "The Threat of Microplastics in Our Oceans",
    "Rewilding: Bringing Back Lost Species to Restore Ecosystems",

    # Business
    "How to Build a Thriving Startup in a Competitive Market",
    "The Future of E-commerce: Trends to Watch in 2025",
    "Strategies for Growing Your Small Business in a Digital World",
    "The Rise of Cryptocurrency: Is Bitcoin the Future of Finance?",
    "How Remote Work is Shaping the Future of Corporate Culture",
    "Navigating the Challenges of Global Supply Chain Disruptions",
    "The Role of Leadership in Driving Business Success",
    "How AI is Revolutionizing the Retail Industry",
    "Understanding the Basics of Venture Capital Funding",
    "How to Create a Successful Marketing Strategy for Your Business",

    # Sports
    "Olympic Games 2024: What to Expect from the World’s Biggest Event",
    "How Data Analytics is Changing the Way Teams Approach Sports",
    "Top Fitness Trends to Improve Athletic Performance in 2024",
    "The Evolution of Women's Soccer: Breaking Barriers and Records",
    "How Esports is Becoming a Billion-Dollar Industry",
    "Sports Psychology: The Key to Unlocking Peak Performance",
    "The Role of Nutrition in Enhancing Athletic Endurance",
    "How VAR Technology is Changing the Game of Football",
    "The Rise of Extreme Sports: Why Athletes Are Pushing the Limits",
    "Top 10 Greatest Moments in Olympic History"
]

start = time.time()

classify_ai = "https://satyam998-introlix-feed-classify.hf.space/classify/"

def classify_article(text):
    classify_ai = "https://satyam998-introlix-feed-classify.hf.space/classify/"
    payload = {"text": text}

    response = requests.post(classify_ai, json=payload)
    response.raise_for_status()
    return response.json().get('category', 'Unknown')

# Function to classify articles in parallel
def classify_articles_parallel(titles):
    classes = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit classification tasks to the executor
        future_to_title = {executor.submit(classify_article, title): title for title in titles}
        
        # Process the results as they complete
        for future in concurrent.futures.as_completed(future_to_title):
            try:
                category = future.result()
                classes.append(category)
            except Exception as exc:
                classes.append('Unknown')  # Handle exceptions gracefully
                print(f"An error occurred: {exc}")
    return classes

classes = classify_articles_parallel(titles)

print(classes)

end = time.time()

time_taken = (end - start) / 60

print(f"Total time takes: {time_taken} minutes")