// supabase/functions/generateEmbedding/index.ts

// Follow Supabase Edge Functions format
// https://supabase.com/docs/guides/functions

import { serve } from 'https://deno.land/std@0.131.0/http/server.ts'
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.0'

const corsHeaders = {
  'Access-Control-Allow-Origin': '*',
  'Access-Control-Allow-Headers': 'authorization, x-client-info, apikey, content-type',
}

interface EmbeddingResponse {
  embedding: number[]
}

serve(async (req) => {
  // Handle CORS preflight request
  if (req.method === 'OPTIONS') {
    return new Response('ok', { headers: corsHeaders })
  }

  try {
    // Get the request body
    const { record, type } = await req.json()

    // Get the API key from the request header
    const apiKey = req.headers.get('Authorization')?.replace('Bearer ', '')
    if (!apiKey) {
      return new Response(
        JSON.stringify({ error: 'Missing Authorization header' }),
        { status: 401, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Create a Supabase client
    const supabaseClient = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      apiKey
    )

    // If there's no text content to embed, return error
    if (!record.text_content) {
      return new Response(
        JSON.stringify({ error: 'Missing text_content in record' }),
        { status: 400, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
      )
    }

    // Call Ollama API to generate embeddings
    // NOTE: In production, you'd use a proper API client or OpenAI SDK
    const ollamaResponse = await fetch('http://localhost:11434/api/embeddings', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        model: 'nomic-embed-text',
        prompt: record.text_content.substring(0, 8000), // Limiting the text length
      }),
    })

    if (!ollamaResponse.ok) {
      const error = await ollamaResponse.text()
      throw new Error(Error from Ollama API: Exception setting "WindowTitle": "Window title cannot be longer than 1023 characters." Exception setting "WindowTitle": "Window title cannot be longer than 1023 characters." Exception setting "WindowTitle": "Window title cannot be longer than 1023 characters." Exception setting "WindowTitle": "Window title cannot be longer than 1023 characters." Exception setting "WindowTitle": "Window title cannot be longer than 1023 characters." A positional parameter cannot be found that accepts argument 'src/supabase'. Cannot find path 'C:\Users\casey\Downloads\chatgpt-your-files-main\chatgpt-your-files-main\ai-warp\ai-warp' because it does not exist. Cannot find path 'C:\Users\casey\Downloads\chatgpt-your-files-main\chatgpt-your-files-main\ai-warp\ai-warp' because it does not exist. The term 'warp' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again. Exception calling "Join" with "2" argument(s): "Value cannot be null. (Parameter 'values')" The term 'supabase' is not recognized as a name of a cmdlet, function, script file, or executable program.
Check the spelling of the name, or if a path was included, verify that the path is correct and try again.)
    }

    const ollamaData = await ollamaResponse.json() as EmbeddingResponse
    
    // Update the record with the embedding
    const { data, error } = await supabaseClient
      .from('pages')
      .update({ embedding: ollamaData.embedding })
      .eq('id', record.id)
      .select()

    if (error) {
      throw error
    }

    return new Response(
      JSON.stringify({ success: true, data }),
      { headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  } catch (error) {
    return new Response(
      JSON.stringify({ error: error.message }),
      { status: 500, headers: { ...corsHeaders, 'Content-Type': 'application/json' } }
    )
  }
})
