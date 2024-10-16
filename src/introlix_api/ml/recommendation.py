import os
import sys
import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from introlix_api.exception import CustomException
from introlix_api.logger import logger
from introlix_api.app.appwrite import get_interests

class Recommendation:
    def __init__(self, user_interests: list, articles: list):
        """
        Recommendation system for articles using sentence-transformers and cosine similarity

        Args:
            user_interests (list): list of user interests
            articles (list): list of all articles
        """
        self.user_interests = user_interests
        self.articles = articles
        self.recommendations = []
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.response = get_interests()
        self.user_interests = [interest['interest'] for interest in self.response]
        self.interest_keywords = {item['interest'].split(':')[1]: item['keywords'] for item in self.response}

    def encode(self, texts: list):
        """
        Function to encode text into embeddings using sentence-transformers

        Args:
            texts (list): list of text to be encoded
        Returns:
            encoded embedding values
        """
        try:
            return self.model.encode(texts)
        except Exception as e:
            raise CustomException(e, sys)
    
    def recommend(self):
        """
        Function to recommend aritcles based on user interests

        Args:
            None
        Returns:
            list of recommended articles
        """

        # Initialize new interests
        new_interests = self.user_interests.copy()  # Start with the old 
        new_interests = [item.split(':')[0] for item in new_interests]


        # Adding keywords to user interests based on existing interests
        for interest in self.user_interests:
            if interest in self.interest_keywords:
                # Append related keywords to new_interests
                new_interests.extend(self.interest_keywords[interest])

        # Remove duplicates if needed
        new_interests = list(set(new_interests))


        # encoding user interests into embeddings
        # print(f"Here is user interest keywords: {self.interest_keywords}")
        user_interests_embeddings = self.encode(new_interests)
        user_interests_embeddings = np.mean(user_interests_embeddings, axis=0)  # Averaging embeddings

        # Reshape user embedding to (1, -1) for compatibility with cosine_similarity
        user_interests_embeddings = user_interests_embeddings.reshape(1, -1)

        # encoding all articles into embeddings
        article_embeddings = self.encode(self.articles)

        # print(f"Shape of user_interests_embeddings: {user_interests_embeddings.shape}")
        # print(f"Shape of article_embeddings: {article_embeddings.shape}")

        # calculate cosine similarity between user interests and all article embeddings
        similarities = cosine_similarity(user_interests_embeddings, article_embeddings).flatten()

        # sort articles based on similarity
        recommended_indices = np.argsort(similarities)[::-1]

        # Get all recommended articles sorted by similarity
        recommended_articles = [self.articles[i] for i in recommended_indices]

        return recommended_articles
