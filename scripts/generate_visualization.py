import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from db.database import SessionLocal
from utils.content_based_recommender import ContentBasedRecommender
from tqdm import tqdm
import time

def generate_visualization():
    db: Session = SessionLocal()
    try:
        print("\n🔄 Starting recommendation visualization process...")
        
        with tqdm(total=5, desc="Overall Progress") as pbar:
           
            recommender = ContentBasedRecommender(db)
            pbar.update(1)
            time.sleep(0.5)  
     

            print("\n📊 Fetching items from database...")
            recommender.fetch_item_data()
            pbar.update(1)
            
           
            print("📝 Processing item descriptions...")
            documents = recommender.create_item_documents()
            pbar.update(1)
            
  
            print("🧠 Training Word2Vec model...")
            recommender.train_word2vec(documents)
            recommender.create_item_embeddings(documents)
            pbar.update(1)
            
       
            print("🎨 Generating visualization...")
            image_path = recommender.visualize_embeddings()
            pbar.update(1)
            
            print(f"\n✨ Visualization saved to: {image_path}")
            
    finally:
        db.close()

if __name__ == "__main__":
    generate_visualization() 