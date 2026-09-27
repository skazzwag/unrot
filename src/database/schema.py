"""DuckDB schema definitions for the unrot brain training app."""

SCHEMA_SQL = """
-- User preferences and configuration
CREATE TABLE IF NOT EXISTS user_preferences (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL,
    default_topics TEXT[],
    default_difficulty TEXT CHECK(default_difficulty IN (
        'beginner', 'intermediate', 'advanced', 'expert', 'mixed'
    )),
    default_question_count INTEGER DEFAULT 10,
    use_web_search BOOLEAN DEFAULT TRUE,
    web_search_recency_months INTEGER DEFAULT 6,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Questions in the bank (MCQ and open-ended)
CREATE TABLE IF NOT EXISTS questions (
    id TEXT PRIMARY KEY,
    topic TEXT NOT NULL,
    subtopic TEXT,
    difficulty TEXT NOT NULL CHECK(difficulty IN (
        'beginner', 'intermediate', 'advanced', 'expert'
    )),
    type TEXT NOT NULL CHECK(type IN ('multiple_choice', 'open_ended')),
    question_text TEXT NOT NULL,
    -- MCQ fields
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_answer TEXT CHECK(correct_answer IS NULL OR correct_answer IN ('A', 'B', 'C', 'D')),
    explanation TEXT,
    why_wrong_a TEXT,
    why_wrong_b TEXT,
    why_wrong_c TEXT,
    why_wrong_d TEXT,
    -- Open-ended fields
    sample_answer TEXT,
    evaluation_criteria TEXT[],
    resources TEXT[],
    -- Metadata
    tags TEXT[],
    source TEXT DEFAULT 'static',
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Provenance tracking for agent-generated questions
CREATE TABLE IF NOT EXISTS question_provenance (
    id TEXT PRIMARY KEY,
    question_id TEXT NOT NULL,
    search_query TEXT,
    source_urls TEXT[],
    model_used TEXT,
    generation_prompt TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (question_id) REFERENCES questions(id)
);

-- Quiz sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER,
    topics TEXT[],
    difficulty TEXT CHECK(difficulty IN (
        'beginner', 'intermediate', 'advanced', 'expert', 'mixed'
    )),
    question_count INTEGER,
    web_search_enabled BOOLEAN,
    web_search_recency_months INTEGER,
    FOREIGN KEY (user_id) REFERENCES user_preferences(id)
);

-- Individual question answers within sessions
CREATE TABLE IF NOT EXISTS session_questions (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    question_id TEXT,
    topic TEXT NOT NULL,
    subtopic TEXT,
    difficulty TEXT NOT NULL,
    type TEXT NOT NULL,
    question_text TEXT NOT NULL,
    option_a TEXT,
    option_b TEXT,
    option_c TEXT,
    option_d TEXT,
    correct_answer TEXT,
    user_answer TEXT,
    is_correct BOOLEAN,
    score INTEGER CHECK(score IS NULL OR score BETWEEN 0 AND 3),
    time_spent_seconds INTEGER,
    feedback TEXT,
    source TEXT,
    source_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

-- Aggregated performance statistics
CREATE TABLE IF NOT EXISTS performance_stats (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,
    topic TEXT NOT NULL,
    subtopic TEXT,
    difficulty TEXT NOT NULL,
    total_questions INTEGER DEFAULT 0,
    correct_questions INTEGER DEFAULT 0,
    total_score INTEGER DEFAULT 0,
    max_score INTEGER DEFAULT 0,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, topic, subtopic, difficulty),
    FOREIGN KEY (user_id) REFERENCES user_preferences(id)
);
"""

DEFAULT_USER_SQL = """
INSERT INTO user_preferences (
    id, username, default_topics, default_difficulty,
    default_question_count, use_web_search, web_search_recency_months
)
SELECT 1, 'default', ['dbt'], 'mixed', 10, TRUE, 6
WHERE NOT EXISTS (SELECT 1 FROM user_preferences WHERE id = 1)
"""


def get_all_schema_sql() -> list[str]:
    """Return all schema SQL statements in order."""
    statements = SCHEMA_SQL.strip().split(";")
    return [s.strip() for s in statements if s.strip()]


def get_default_user_sql() -> str:
    """Return the default user insert SQL."""
    return DEFAULT_USER_SQL.strip()
