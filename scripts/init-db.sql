-- Create user service database schema
CREATE SCHEMA IF NOT EXISTS user_service;

-- Create initial tables
CREATE TABLE IF NOT EXISTS user_service.users (
    id SERIAL PRIMARY KEY,
    external_id VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_service.user_profiles (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_service.users(id) ON DELETE CASCADE,
    age INTEGER,
    gender VARCHAR(50),
    location VARCHAR(255),
    interests TEXT,
    metadata JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_service.user_interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_service.users(id) ON DELETE CASCADE,
    item_id VARCHAR(255) NOT NULL,
    interaction_type VARCHAR(50) NOT NULL,
    rating DECIMAL(3,2),
    metadata JSONB,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS user_service.user_preferences (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES user_service.users(id) ON DELETE CASCADE,
    category VARCHAR(255) NOT NULL,
    weight DECIMAL(3,2) DEFAULT 0.5,
    tags JSONB,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX idx_users_external_id ON user_service.users(external_id);
CREATE INDEX idx_interactions_user_timestamp ON user_service.user_interactions(user_id, timestamp DESC);
CREATE INDEX idx_preferences_user_category ON user_service.user_preferences(user_id, category);