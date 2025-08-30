"""
Collaborative Filtering Implementation
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import TruncatedSVD
import logging

logger = logging.getLogger(__name__)


class CollaborativeFilter:
    """User-Item Collaborative Filtering with Matrix Factorization"""
    
    def __init__(self, n_factors: int = 50, min_interactions: int = 5):
        self.n_factors = n_factors
        self.min_interactions = min_interactions
        self.svd = TruncatedSVD(n_components=n_factors, random_state=42)
        self.user_item_matrix = None
        self.user_factors = None
        self.item_factors = None
        self.user_means = None
        self.global_mean = 0.0
        self.user_to_idx = {}
        self.idx_to_user = {}
        self.item_to_idx = {}
        self.idx_to_item = {}
        self.is_fitted = False
    
    def _create_user_item_matrix(self, interactions: pd.DataFrame) -> np.ndarray:
        """Create user-item interaction matrix"""
        # Filter users/items with minimum interactions
        user_counts = interactions['user_id'].value_counts()
        item_counts = interactions['item_id'].value_counts()
        
        valid_users = user_counts[user_counts >= self.min_interactions].index
        valid_items = item_counts[item_counts >= self.min_interactions].index
        
        interactions = interactions[
            interactions['user_id'].isin(valid_users) & 
            interactions['item_id'].isin(valid_items)
        ]
        
        # Create mappings
        unique_users = sorted(interactions['user_id'].unique())
        unique_items = sorted(interactions['item_id'].unique())
        
        self.user_to_idx = {user: idx for idx, user in enumerate(unique_users)}
        self.idx_to_user = {idx: user for user, idx in self.user_to_idx.items()}
        self.item_to_idx = {item: idx for idx, item in enumerate(unique_items)}
        self.idx_to_item = {idx: item for item, idx in self.item_to_idx.items()}
        
        # Create matrix
        n_users = len(unique_users)
        n_items = len(unique_items)
        matrix = np.zeros((n_users, n_items))
        
        for _, row in interactions.iterrows():
            if row['rating'] is not None:
                user_idx = self.user_to_idx[row['user_id']]
                item_idx = self.item_to_idx[row['item_id']]
                matrix[user_idx, item_idx] = row['rating']
        
        return matrix
    
    def fit(self, interactions: pd.DataFrame):
        """Train the collaborative filtering model"""
        logger.info(f"Training CF model with {len(interactions)} interactions")
        
        self.user_item_matrix = self._create_user_item_matrix(interactions)
        
        if self.user_item_matrix.size == 0:
            logger.warning("Empty user-item matrix after filtering")
            return
        
        # Calculate means
        self.global_mean = np.mean(self.user_item_matrix[self.user_item_matrix > 0])
        self.user_means = {}
        
        for user_idx in range(self.user_item_matrix.shape[0]):
            user_ratings = self.user_item_matrix[user_idx, self.user_item_matrix[user_idx] > 0]
            if len(user_ratings) > 0:
                self.user_means[user_idx] = np.mean(user_ratings)
            else:
                self.user_means[user_idx] = self.global_mean
        
        # Apply SVD
        # Replace zeros with user means for better factorization
        matrix_filled = self.user_item_matrix.copy()
        for user_idx in range(matrix_filled.shape[0]):
            zero_mask = matrix_filled[user_idx] == 0
            matrix_filled[user_idx, zero_mask] = self.user_means[user_idx]
        
        self.user_factors = self.svd.fit_transform(matrix_filled)
        self.item_factors = self.svd.components_.T
        
        self.is_fitted = True
        logger.info(f"CF model trained: {self.user_factors.shape[0]} users, {self.item_factors.shape[0]} items")
    
    def predict_rating(self, user_id: int, item_id: int) -> float:
        """Predict rating for user-item pair"""
        if not self.is_fitted:
            return self.global_mean
        
        if user_id not in self.user_to_idx or item_id not in self.item_to_idx:
            return self.global_mean
        
        user_idx = self.user_to_idx[user_id]
        item_idx = self.item_to_idx[item_id]
        
        # Matrix factorization prediction
        prediction = np.dot(self.user_factors[user_idx], self.item_factors[item_idx])
        
        # Bound prediction between 1 and 5
        return max(1.0, min(5.0, prediction))
    
    def get_user_recommendations(self, user_id: int, n_recommendations: int = 10, 
                               exclude_seen: bool = True) -> List[Tuple[int, float]]:
        """Get top N recommendations for a user"""
        if not self.is_fitted or user_id not in self.user_to_idx:
            return []
        
        user_idx = self.user_to_idx[user_id]
        
        # Get predictions for all items
        predictions = []
        seen_items = set()
        
        if exclude_seen:
            # Get items user has already interacted with
            user_row = self.user_item_matrix[user_idx]
            seen_items = set(np.where(user_row > 0)[0])
        
        for item_idx in range(len(self.idx_to_item)):
            if item_idx not in seen_items:
                item_id = self.idx_to_item[item_idx]
                score = self.predict_rating(user_id, item_id)
                predictions.append((item_id, score))
        
        # Sort by score and return top N
        predictions.sort(key=lambda x: x[1], reverse=True)
        return predictions[:n_recommendations]
    
    def get_similar_users(self, user_id: int, n_similar: int = 10) -> List[Tuple[int, float]]:
        """Find similar users using cosine similarity"""
        if not self.is_fitted or user_id not in self.user_to_idx:
            return []
        
        user_idx = self.user_to_idx[user_id]
        user_vector = self.user_factors[user_idx].reshape(1, -1)
        
        # Calculate similarities
        similarities = cosine_similarity(user_vector, self.user_factors)[0]
        
        # Get top similar users (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar+1]
        
        return [(self.idx_to_user[idx], similarities[idx]) for idx in similar_indices]
    
    def get_similar_items(self, item_id: int, n_similar: int = 10) -> List[Tuple[int, float]]:
        """Find similar items using cosine similarity"""
        if not self.is_fitted or item_id not in self.item_to_idx:
            return []
        
        item_idx = self.item_to_idx[item_id]
        item_vector = self.item_factors[item_idx].reshape(1, -1)
        
        # Calculate similarities
        similarities = cosine_similarity(item_vector, self.item_factors)[0]
        
        # Get top similar items (excluding self)
        similar_indices = np.argsort(similarities)[::-1][1:n_similar+1]
        
        return [(self.idx_to_item[idx], similarities[idx]) for idx in similar_indices]


class UserBasedCF:
    """User-based Collaborative Filtering"""
    
    def __init__(self, min_common_items: int = 3, similarity_threshold: float = 0.1):
        self.min_common_items = min_common_items
        self.similarity_threshold = similarity_threshold
        self.user_item_matrix = None
        self.user_similarities = {}
        self.is_fitted = False
    
    def fit(self, interactions: pd.DataFrame):
        """Train user-based CF model"""
        # Create user-item matrix
        self.user_item_matrix = interactions.pivot_table(
            index='user_id', 
            columns='item_id', 
            values='rating',
            fill_value=0
        )
        
        # Calculate user similarities
        users = self.user_item_matrix.index.tolist()
        
        for i, user1 in enumerate(users):
            self.user_similarities[user1] = {}
            user1_ratings = self.user_item_matrix.loc[user1]
            
            for j, user2 in enumerate(users[i+1:], i+1):
                user2_ratings = self.user_item_matrix.loc[user2]
                
                # Find common items
                common_items = (user1_ratings > 0) & (user2_ratings > 0)
                
                if common_items.sum() >= self.min_common_items:
                    # Calculate cosine similarity
                    similarity = cosine_similarity(
                        user1_ratings.values.reshape(1, -1),
                        user2_ratings.values.reshape(1, -1)
                    )[0][0]
                    
                    if similarity > self.similarity_threshold:
                        self.user_similarities[user1][user2] = similarity
                        if user2 not in self.user_similarities:
                            self.user_similarities[user2] = {}
                        self.user_similarities[user2][user1] = similarity
        
        self.is_fitted = True
        logger.info(f"User-based CF trained with {len(users)} users")
    
    def get_recommendations(self, user_id: int, n_recommendations: int = 10) -> List[Tuple[int, float]]:
        """Get recommendations based on similar users"""
        if not self.is_fitted or user_id not in self.user_similarities:
            return []
        
        # Get similar users
        similar_users = self.user_similarities[user_id]
        
        if not similar_users:
            return []
        
        # Get items rated by similar users
        item_scores = {}
        user_ratings = self.user_item_matrix.loc[user_id]
        
        for similar_user, similarity in similar_users.items():
            similar_user_ratings = self.user_item_matrix.loc[similar_user]
            
            for item_id, rating in similar_user_ratings.items():
                if rating > 0 and user_ratings[item_id] == 0:  # User hasn't seen this item
                    if item_id not in item_scores:
                        item_scores[item_id] = 0
                    item_scores[item_id] += similarity * rating
        
        # Sort and return top recommendations
        recommendations = sorted(item_scores.items(), key=lambda x: x[1], reverse=True)
        return recommendations[:n_recommendations]