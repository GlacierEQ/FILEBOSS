-- OpenDevin Enhanced Supabase Schema
-- Run this in your Supabase SQL editor to set up the required tables

-- Enable necessary extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- Users table for authentication and user management
CREATE TABLE IF NOT EXISTS public.users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    username TEXT UNIQUE,
    full_name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Projects table for managing coding projects
CREATE TABLE IF NOT EXISTS public.projects (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name TEXT NOT NULL,
    description TEXT,
    owner_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    workspace_path TEXT,
    repository_url TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Sessions table for tracking AI agent sessions
CREATE TABLE IF NOT EXISTS public.sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
    agent_type TEXT NOT NULL DEFAULT 'MonologueAgent',
    llm_model TEXT NOT NULL DEFAULT 'ollama/codellama:7b-instruct',
    status TEXT NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'paused', 'completed', 'error')),
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    metadata JSONB DEFAULT '{}'
);

-- Messages table for storing conversation history
CREATE TABLE IF NOT EXISTS public.messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text', 'code', 'command', 'file', 'error')),
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Files table for tracking file changes and versions
CREATE TABLE IF NOT EXISTS public.files (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    content TEXT,
    content_hash TEXT,
    operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'delete', 'read')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Code analysis table for storing AI-generated insights
CREATE TABLE IF NOT EXISTS public.code_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    analysis_type TEXT NOT NULL CHECK (analysis_type IN ('complexity', 'bugs', 'suggestions', 'documentation')),
    analysis_result JSONB NOT NULL,
    confidence_score DECIMAL(3,2) DEFAULT 0.8,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Commands table for tracking executed commands
CREATE TABLE IF NOT EXISTS public.commands (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    command TEXT NOT NULL,
    output TEXT,
    exit_code INTEGER,
    execution_time INTERVAL,
    executed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Collaborative editing table for real-time collaboration
CREATE TABLE IF NOT EXISTS public.collaborative_edits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    user_id UUID REFERENCES public.users(id) ON DELETE CASCADE,
    file_path TEXT NOT NULL,
    operation JSONB NOT NULL, -- Store OT (Operational Transform) operations
    timestamp TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    applied BOOLEAN DEFAULT FALSE
);

-- Model usage tracking for analytics
CREATE TABLE IF NOT EXISTS public.model_usage (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID REFERENCES public.sessions(id) ON DELETE CASCADE,
    model_name TEXT NOT NULL,
    provider TEXT NOT NULL DEFAULT 'ollama',
    tokens_input INTEGER DEFAULT 0,
    tokens_output INTEGER DEFAULT 0,
    response_time INTERVAL,
    cost DECIMAL(10,6) DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON public.sessions(user_id);
CREATE INDEX IF NOT EXISTS idx_sessions_project_id ON public.sessions(project_id);
CREATE INDEX IF NOT EXISTS idx_messages_session_id ON public.messages(session_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON public.messages(created_at);
CREATE INDEX IF NOT EXISTS idx_files_session_id ON public.files(session_id);
CREATE INDEX IF NOT EXISTS idx_files_file_path ON public.files(file_path);
CREATE INDEX IF NOT EXISTS idx_commands_session_id ON public.commands(session_id);
CREATE INDEX IF NOT EXISTS idx_collaborative_edits_session_id ON public.collaborative_edits(session_id);
CREATE INDEX IF NOT EXISTS idx_model_usage_session_id ON public.model_usage(session_id);

-- Enable Row Level Security (RLS)
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.files ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.code_analysis ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.commands ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.collaborative_edits ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.model_usage ENABLE ROW LEVEL SECURITY;

-- Create RLS policies

-- Users can only see and modify their own data
CREATE POLICY "Users can view own profile" ON public.users
    FOR SELECT USING (auth.uid() = id);

CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (auth.uid() = id);

-- Project access policies
CREATE POLICY "Users can view own projects" ON public.projects
    FOR SELECT USING (auth.uid() = owner_id OR is_public = true);

CREATE POLICY "Users can create projects" ON public.projects
    FOR INSERT WITH CHECK (auth.uid() = owner_id);

CREATE POLICY "Users can update own projects" ON public.projects
    FOR UPDATE USING (auth.uid() = owner_id);

CREATE POLICY "Users can delete own projects" ON public.projects
    FOR DELETE USING (auth.uid() = owner_id);

-- Session access policies
CREATE POLICY "Users can view own sessions" ON public.sessions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can create sessions" ON public.sessions
    FOR INSERT WITH CHECK (auth.uid() = user_id);

CREATE POLICY "Users can update own sessions" ON public.sessions
    FOR UPDATE USING (auth.uid() = user_id);

-- Message access policies
CREATE POLICY "Users can view messages from own sessions" ON public.messages
    FOR SELECT USING (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can create messages in own sessions" ON public.messages
    FOR INSERT WITH CHECK (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

-- File access policies
CREATE POLICY "Users can view files from own sessions" ON public.files
    FOR SELECT USING (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can create files in own sessions" ON public.files
    FOR INSERT WITH CHECK (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

-- Similar policies for other tables
CREATE POLICY "Users can view own code analysis" ON public.code_analysis
    FOR SELECT USING (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can create code analysis in own sessions" ON public.code_analysis
    FOR INSERT WITH CHECK (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can view own commands" ON public.commands
    FOR SELECT USING (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can create commands in own sessions" ON public.commands
    FOR INSERT WITH CHECK (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can view collaborative edits from own sessions" ON public.collaborative_edits
    FOR SELECT USING (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can create collaborative edits in own sessions" ON public.collaborative_edits
    FOR INSERT WITH CHECK (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can view own model usage" ON public.model_usage
    FOR SELECT USING (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

CREATE POLICY "Users can create model usage in own sessions" ON public.model_usage
    FOR INSERT WITH CHECK (auth.uid() IN (
        SELECT user_id FROM public.sessions WHERE id = session_id
    ));

-- Create functions for updated_at timestamps
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON public.projects
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create a function to handle user registration
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO public.users (id, email, username, full_name, avatar_url)
    VALUES (
        NEW.id,
        NEW.email,
        NEW.raw_user_meta_data->>'username',
        NEW.raw_user_meta_data->>'full_name',
        NEW.raw_user_meta_data->>'avatar_url'
    );
    RETURN NEW;
END;
$$ language plpgsql security definer;

-- Create trigger for new user registration
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL TABLES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;
GRANT ALL ON ALL FUNCTIONS IN SCHEMA public TO anon, authenticated;

-- Create a view for session summaries
CREATE OR REPLACE VIEW public.session_summaries AS
SELECT 
    s.id,
    s.user_id,
    s.project_id,
    s.agent_type,
    s.llm_model,
    s.status,
    s.started_at,
    s.ended_at,
    p.name as project_name,
    COUNT(m.id) as message_count,
    COUNT(DISTINCT f.file_path) as files_modified,
    COUNT(c.id) as commands_executed
FROM public.sessions s
LEFT JOIN public.projects p ON s.project_id = p.id
LEFT JOIN public.messages m ON s.id = m.session_id
LEFT JOIN public.files f ON s.id = f.session_id
LEFT JOIN public.commands c ON s.id = c.session_id
GROUP BY s.id, s.user_id, s.project_id, s.agent_type, s.llm_model, s.status, s.started_at, s.ended_at, p.name;

-- Enable realtime for tables that need it
ALTER PUBLICATION supabase_realtime ADD TABLE public.messages;
ALTER PUBLICATION supabase_realtime ADD TABLE public.collaborative_edits;
ALTER PUBLICATION supabase_realtime ADD TABLE public.sessions;

COMMIT;

