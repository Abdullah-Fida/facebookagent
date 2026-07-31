-- Run this in your Supabase SQL Editor to create the articles table for the Website Ecosystem

CREATE TABLE public.articles (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    title TEXT NOT NULL,
    slug TEXT NOT NULL UNIQUE,
    content TEXT NOT NULL,
    summary TEXT,
    main_image_url TEXT,
    category TEXT DEFAULT 'News',
    seo_keywords TEXT[],
    published_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    author TEXT DEFAULT 'NOVE NewsAgent'
);

-- Allow anonymous read access so the website can fetch articles
ALTER TABLE public.articles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Allow public read access on articles" 
ON public.articles 
FOR SELECT 
USING (true);

-- Allow the Python backend (which uses the Service Key or authenticated client) to insert/update
CREATE POLICY "Allow authenticated insert on articles" 
ON public.articles 
FOR INSERT 
WITH CHECK (auth.role() = 'authenticated' OR auth.role() = 'service_role');

CREATE POLICY "Allow authenticated update on articles" 
ON public.articles 
FOR UPDATE 
USING (auth.role() = 'authenticated' OR auth.role() = 'service_role');
