-- Database initialization for Real-time Recommendation Engine
-- This script creates the basic schema for Phase 1

-- Create database if it doesn't exist (handled by Docker environment)

-- Users table
CREATE TABLE IF NOT EXISTS users (
    user_id SERIAL PRIMARY KEY,
    age_group VARCHAR(20),
    preferred_categories TEXT[],
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_premium BOOLEAN DEFAULT FALSE,
    location VARCHAR(10),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Items/Content table
CREATE TABLE IF NOT EXISTS items (
    item_id SERIAL PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    category VARCHAR(50),
    features JSONB,
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User interactions table
CREATE TABLE IF NOT EXISTS interactions (
    interaction_id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    item_id INTEGER REFERENCES items(item_id),
    interaction_type VARCHAR(20) NOT NULL,
    rating DECIMAL(2,1),
    session_id VARCHAR(50),
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User profiles (for ML features)
CREATE TABLE IF NOT EXISTS user_profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(user_id),
    interaction_count INTEGER DEFAULT 0,
    avg_rating DECIMAL(3,2),
    favorite_categories TEXT[],
    last_activity TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Item features (for content-based filtering)
CREATE TABLE IF NOT EXISTS item_features (
    item_id INTEGER PRIMARY KEY REFERENCES items(item_id),
    popularity_score DECIMAL(3,2) DEFAULT 0.0,
    avg_rating DECIMAL(3,2),
    interaction_count INTEGER DEFAULT 0,
    feature_vector JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Recommendations cache table
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(user_id),
    item_id INTEGER REFERENCES items(item_id),
    score DECIMAL(4,3),
    algorithm VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_interactions_user_id ON interactions(user_id);
CREATE INDEX IF NOT EXISTS idx_interactions_item_id ON interactions(item_id);
CREATE INDEX IF NOT EXISTS idx_interactions_timestamp ON interactions(timestamp);
CREATE INDEX IF NOT EXISTS idx_interactions_type ON interactions(interaction_type);
CREATE INDEX IF NOT EXISTS idx_recommendations_user_id ON recommendations(user_id);
CREATE INDEX IF NOT EXISTS idx_recommendations_score ON recommendations(score DESC);
CREATE INDEX IF NOT EXISTS idx_items_category ON items(category);
CREATE INDEX IF NOT EXISTS idx_items_features ON items USING GIN (features);

-- Insert some sample data for testing
INSERT INTO users (age_group, preferred_categories, is_premium, location) 
VALUES 
    ('26-35', '{"technology", "movies"}', true, 'US'),
    ('18-25', '{"music", "sports"}', false, 'CA'),
    ('36-45', '{"books", "travel"}', true, 'UK')
ON CONFLICT (user_id) DO NOTHING;

INSERT INTO items (title, category, features)
VALUES 
    ('Sample Movie', 'movies', '{"genre": "action", "rating": 4.5, "year": 2023}'),
    ('Tech Article', 'technology', '{"difficulty": "beginner", "rating": 4.2}'),
    ('Music Album', 'music', '{"genre": "rock", "artist": "Sample Band", "rating": 4.8}')
ON CONFLICT (item_id) DO NOTHING;

-- Create a function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at columns
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_items_updated_at BEFORE UPDATE ON items
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_profiles_updated_at BEFORE UPDATE ON user_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_item_features_updated_at BEFORE UPDATE ON item_features
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Grant permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO recuser;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO recuser;