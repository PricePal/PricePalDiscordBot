import gensim
import numpy as np
import pandas as pd
from sklearn.manifold import TSNE
import matplotlib.pyplot as plt
from sklearn.metrics.pairwise import cosine_similarity
import json
from db.repositories import get_wishlist_items_for_user, get_recent_queries_by_user
from db.models import RecommendedItem

class ContentBasedRecommender:
    def __init__(self, db_session):
        self.db = db_session
        self.item_embeddings = {}
        self.word_model = None
        self.item_data = {}
        
    def fetch_item_data(self):
        """Fetch all items from the database to train embeddings"""
        # Get all recommended items (could also include catalog items if available)
        all_items = self.db.query(RecommendedItem).all()
        
        # Store for later use
        for item in all_items:
            item_id = str(item.id)
            self.item_data[item_id] = {
                'id': item_id,
                'item_name': item.item_name,
                'vendor': item.vendor,
                'price': float(item.price) if item.price else 0.0,
                'metadata': item.item_metadata if item.item_metadata else {}
            }
        
        return self.item_data
    
    def create_item_documents(self):
        """Create text documents for each item by combining name, vendor, and metadata"""
        documents = {}
        
        for item_id, item in self.item_data.items():
            # Combine all text attributes
            doc = f"{item['item_name']} {item['vendor']} "
            
            # Add any metadata text
            if 'metadata' in item and item['metadata']:
                metadata = item['metadata']
                if isinstance(metadata, str):
                    try:
                        metadata = json.loads(metadata)
                    except:
                        metadata = {}
                        
                for key, value in metadata.items():
                    if isinstance(value, str):
                        doc += f"{key} {value} "
            
            # Store the processed document
            documents[item_id] = doc.lower()
            
        return documents
    
    def train_word2vec(self, documents, vector_size=100):
        """Train a Word2Vec model on all item documents"""
        # Prepare corpus
        corpus = [doc.split() for doc in documents.values()]
        
        # Train model
        self.word_model = gensim.models.Word2Vec(
            corpus, 
            vector_size=vector_size,
            window=5, 
            min_count=1, 
            sg=1  # Skip-gram model
        )
        
        print(f"Word2Vec model trained on {len(corpus)} documents")
        return self.word_model
    
    def create_item_embeddings(self, documents):
        """Create item embeddings by averaging word vectors for each document"""
        for item_id, doc in documents.items():
            words = doc.split()
            word_vectors = [self.word_model.wv[word] for word in words if word in self.word_model.wv]
            
            if word_vectors:
                # Average the word vectors to get a document vector
                self.item_embeddings[item_id] = np.mean(word_vectors, axis=0)
            else:
                # Fallback for items without valid words
                self.item_embeddings[item_id] = np.zeros(self.word_model.vector_size)
        
        print(f"Created embeddings for {len(self.item_embeddings)} items")
        return self.item_embeddings
    
    def create_user_profile(self, user_id):
        """Create a user profile vector based on wishlist items and search history"""
        # Get user's wishlist items
        wishlist_items = get_wishlist_items_for_user(self.db, user_id)
        wishlist_ids = [str(item.id) for item in wishlist_items]
        
        # Get user's search queries
        recent_queries = get_recent_queries_by_user(self.db, user_id, limit=10)
        
        # Create embedding from wishlist items
        wishlist_vectors = [
            self.item_embeddings[item_id] for item_id in wishlist_ids 
            if item_id in self.item_embeddings
        ]
        
        # Create embeddings from search queries
        query_vectors = []
        for query in recent_queries:
            query_text = query.raw_query if query.raw_query else ""
            if query_text:
                words = query_text.lower().split()
                word_vecs = [self.word_model.wv[word] for word in words if word in self.word_model.wv]
                if word_vecs:
                    query_vectors.append(np.mean(word_vecs, axis=0))
        
        # Combine wishlist and query vectors (with more weight on wishlist)
        all_vectors = wishlist_vectors + query_vectors
        if all_vectors:
            user_profile = np.mean(all_vectors, axis=0)
        else:
            # Fallback for users with no data
            user_profile = np.zeros(self.word_model.vector_size)
            
        return user_profile
    
    def get_recommendations(self, user_id, n=5):
        """Get top N recommendations for a user"""
        # Create user profile
        user_profile = self.create_user_profile(user_id)
        
        # Calculate similarity to all items
        similarities = {}
        for item_id, item_vec in self.item_embeddings.items():
            # Skip items already in user's wishlist
            wishlist_items = get_wishlist_items_for_user(self.db, user_id)
            wishlist_ids = [str(item.id) for item in wishlist_items]
            if item_id in wishlist_ids:
                continue
                
            # Calculate cosine similarity
            sim = cosine_similarity([user_profile], [item_vec])[0][0]
            similarities[item_id] = sim
            
        # Get top N recommendations
        top_items = sorted(similarities.items(), key=lambda x: x[1], reverse=True)[:n]
        
        # Format results
        recommendations = []
        for item_id, score in top_items:
            item_data = self.item_data.get(item_id, {})
            recommendations.append({
                'item_id': item_id,
                'item_name': item_data.get('item_name', 'Unknown'),
                'vendor': item_data.get('vendor', 'Unknown'),
                'price': item_data.get('price', 0.0),
                'similarity_score': float(score)
            })
            
        return recommendations
    
    def visualize_embeddings(self, highlight_items=None):
        """Create a visualization of item embeddings using t-SNE"""
        # Extract item vectors and IDs
        item_ids = list(self.item_embeddings.keys())
        item_vecs = np.array([self.item_embeddings[item_id] for item_id in item_ids])
        
        # Reduce to 2D for visualization
        tsne = TSNE(n_components=2, random_state=42)
        reduced_vecs = tsne.fit_transform(item_vecs)
        
        # Create plot
        plt.figure(figsize=(12, 10))
        
        # Plot all items
        plt.scatter(reduced_vecs[:, 0], reduced_vecs[:, 1], alpha=0.5)
        
        # Highlight specific items if provided
        if highlight_items:
            highlight_indices = [item_ids.index(item_id) for item_id in highlight_items if item_id in item_ids]
            plt.scatter(
                reduced_vecs[highlight_indices, 0], 
                reduced_vecs[highlight_indices, 1], 
                color='red', 
                alpha=1, 
                s=100
            )
        
        # Add item names as labels
        for i, item_id in enumerate(item_ids):
            item_name = self.item_data.get(item_id, {}).get('item_name', '')
            plt.annotate(
                item_name[:20] + '...' if len(item_name) > 20 else item_name,
                (reduced_vecs[i, 0], reduced_vecs[i, 1]),
                fontsize=8,
                alpha=0.7
            )
        
        plt.title('Item Embedding Space Visualization')
        plt.tight_layout()
        
        # Save the visualization
        plt.savefig('item_embeddings.png', dpi=300)
        return 'item_embeddings.png'
