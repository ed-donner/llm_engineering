require_relative 'initializer'

chat_history = [
  { role: "system", content: "You are helpful assistant. If you do not know the answer, do not make it up, just say you do not know." }
]
openai = OpenAI::Client.new(uri_base: 'http://localhost:11434/v1', access_token: 'ollama') # LLaMa locally

def get_embeddings(text, client)
  response = client.embeddings(parameters: { model: "llama3.2", input: text })
  response["data"].first["embedding"]
end

def build_prompt(chat_history:, context_chunks:, user_message:)
  context_text = context_chunks.join("\n---\n")

  <<~PROMPT
    Here is an additional context from our knowledge base:
    #{context_text}

    New question from a user:
    User: #{user_message}

    Please answer using the context above.
  PROMPT
end

collection_name = "my_collection"
collection = Chroma::Resources::Collection.get(collection_name)

puts "Welcome to our little experiment!"

while true
  user_message = gets.chomp

  if user_message == 'exit'
    puts "Ending the session"
    exit 0
  end

  query_embedding = get_embeddings(user_message, openai)
  results = collection.query(query_embeddings: [query_embedding], results: 15)
  retrieved_chunks = results.map(&:document)

  prompt = build_prompt(
    chat_history: chat_history,
    context_chunks: retrieved_chunks,
    user_message: user_message
  )
  chat_history << { role: "user", content: prompt }

  response_message = ""
  openai.chat(parameters: {
    model: "llama3.2",
    messages: chat_history,
    stream: proc { |chunk, _bytesize|
      delta = chunk.dig("choices", 0, "delta", "content")
      next unless delta
      print delta
      response_message << delta
    }
  })
  chat_history << { role: "assistant", content: response_message }
  puts
end




