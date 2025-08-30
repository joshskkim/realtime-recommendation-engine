#!/usr/bin/env python3
"""
Generate sample data for the recommendation engine
"""

import json
import random
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any
import argparse

# Configuration
USERS_COUNT = 1000
ITEMS_COUNT = 5000
INTERACTIONS_COUNT = 50000
OUTPUT_DIR = "datasets/generated"

def generate_users(count: int) -> List[Dict[str, Any]]:
    """Generate sample users"""
    categories = ["technology", "sports", "movies", "books", "music", "travel", "food"]
    demographics = ["18-25", "26-35", "36-45", "46-55", "55+"]
    
    users = []
    for i in range(1, count + 1):
        user = {
            "user_id": i,
            "age_group": random.choice(demographics),
            "preferred_categories": random.sample(categories, k=random.randint(1, 3)),
            "registration_date": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "is_premium": random.random() < 0.3,
            "location": random.choice(["US", "CA", "UK", "DE", "FR", "JP", "AU"])
        }
        users.append(user)
    
    return users

def generate_items(count: int) -> List[Dict[str, Any]]:
    """Generate sample items"""
    categories = ["technology", "sports", "movies", "books", "music", "travel", "food"]
    
    items = []
    for i in range(1, count + 1):
        item = {
            "item_id": i,
            "title": f"Item {i}",
            "category": random.choice(categories),
            "features": {
                "genre": random.choice(["action", "comedy", "drama", "sci-fi", "documentary"]),
                "rating": round(random.uniform(1.0, 5.0), 1),
                "popularity_score": round(random.uniform(0.1, 1.0), 2),
                "release_year": random.randint(2020, 2024)
            },
            "created_date": (datetime.now() - timedelta(days=random.randint(1, 180))).isoformat()
        }
        items.append(item)
    
    return items

def generate_interactions(users_count: int, items_count: int, count: int) -> List[Dict[str, Any]]:
    """Generate sample user interactions"""
    interaction_types = ["view", "like", "dislike", "share", "purchase", "rating"]
    
    interactions = []
    for i in range(count):
        interaction = {
            "interaction_id": i + 1,
            "user_id": random.randint(1, users_count),
            "item_id": random.randint(1, items_count),
            "interaction_type": random.choice(interaction_types),
            "timestamp": (datetime.now() - timedelta(
                days=random.randint(0, 30),
                hours=random.randint(0, 23),
                minutes=random.randint(0, 59)
            )).isoformat(),
            "rating": random.uniform(1.0, 5.0) if random.random() < 0.4 else None,
            "session_id": f"session_{random.randint(1, 10000)}"
        }
        interactions.append(interaction)
    
    return interactions

def save_json(data: List[Dict], filename: str, output_dir: str):
    """Save data to JSON file"""
    os.makedirs(output_dir, exist_ok=True)
    filepath = os.path.join(output_dir, filename)
    
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"✅ Generated {filename} with {len(data)} records")

def main():
    parser = argparse.ArgumentParser(description='Generate sample data for recommendation engine')
    parser.add_argument('--users', type=int, default=USERS_COUNT, help='Number of users')
    parser.add_argument('--items', type=int, default=ITEMS_COUNT, help='Number of items')
    parser.add_argument('--interactions', type=int, default=INTERACTIONS_COUNT, help='Number of interactions')
    parser.add_argument('--output', type=str, default=OUTPUT_DIR, help='Output directory')
    
    args = parser.parse_args()
    
    print(f"🚀 Generating sample data...")
    print(f"Users: {args.users}, Items: {args.items}, Interactions: {args.interactions}")
    
    # Set random seed for reproducible data
    random.seed(42)
    
    # Generate data
    users = generate_users(args.users)
    items = generate_items(args.items)
    interactions = generate_interactions(args.users, args.items, args.interactions)
    
    # Save to files
    save_json(users, "users.json", args.output)
    save_json(items, "items.json", args.output)
    save_json(interactions, "interactions.json", args.output)
    
    print(f"✅ Sample data generation complete!")
    print(f"📁 Files saved to: {args.output}")

if __name__ == "__main__":
    main()