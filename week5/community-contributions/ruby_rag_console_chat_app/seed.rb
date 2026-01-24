require_relative 'initializer'
require 'pragmatic_segmenter'

folders = Dir.glob("knowledge_base/*").select { |f| File.directory?(f) }

documents = []

folders.each do |folder|
  doc_type = File.basename(folder)
  Dir.glob("#{folder}/**/*.md").each do |filepath|
    content = File.read(filepath, encoding: 'utf-8')
    doc = {
      content: content,
      path: filepath,
      metadata: { "doc_type" => doc_type }
    }
    documents << doc
  end
end

# chunk_size and chunk_overlap are configurable for getting better results
def split_text(text, chunk_size: 1000, chunk_overlap: 200)
  chunks = []
  start = 0
  while start < text.length
    finish = [start + chunk_size, text.length].min
    chunks << text[start...finish]
    break if finish == text.length
    start += (chunk_size - chunk_overlap)
  end
  chunks
end

def split_text_by_sentence(text, chunk_size: 1500, chunk_overlap: 200)
  ps = PragmaticSegmenter::Segmenter.new(text: text)
  sentences = ps.segment
  chunks = []
  current_chunk = ""
  sentences.each do |sentence|
    if (current_chunk + sentence).length > chunk_size
      chunks << current_chunk.strip
      # For overlap, take last N chars from current_chunk (optionally at sentence boundary)
      overlap = current_chunk[-chunk_overlap..-1] || ""
      current_chunk = overlap + sentence
    else
      current_chunk += " " unless current_chunk.empty?
      current_chunk += sentence
    end
  end
  chunks << current_chunk.strip unless current_chunk.empty?
  chunks
end

chunks = []

# documents.each do |doc|
#   split_text(doc[:content]).each_with_index do |chunk, idx|
#     chunks << {
#       content: chunk,
#       metadata: doc[:metadata].merge({ "chunk_index" => idx, "path" => doc[:path] })
#     }
#   end
# end

documents.each do |doc|
  split_text_by_sentence(doc[:content]).each_with_index do |chunk, idx|
    chunks << {
      content: chunk,
      metadata: doc[:metadata].merge({ "chunk_index" => idx, "path" => doc[:path] })
    }
  end
end

puts "Chucks count: #{chunks.count}"
puts "Document types found: #{chunks.map { _1[:metadata]['doc_type']}.uniq.join(', ') }"

# 1. Set up OpenAI client (replace with RubyLLM or HTTP if using HuggingFace)
# openai = OpenAI::Client.new(access_token: ENV['OPENAI_API_KEY']) # OpenAI API, remotely
openai = OpenAI::Client.new(uri_base: 'http://localhost:11434/v1', access_token: 'ollama') # LLaMa, locally

# 2. Get embeddings for each chunk
def get_embedding(text, client)
  response = client.embeddings(parameters: { model: "llama3.2", input: text })
  response["data"].first["embedding"]
end

# Check current Chrome server version
version = Chroma::Resources::Database.version
puts version

collection_name = "my_collection"
collection = begin
  Chroma::Resources::Collection.get(collection_name)
rescue Chroma::APIError => e
  nil
end

if collection
  puts "Collection already exists"
  puts "Do you want to reset it? (y/n)"
  answer = gets.chomp
  if answer == 'y'
    Chroma::Resources::Collection.delete(collection_name)
    puts 'Collection deleted'
    exit 0
  end
end

puts "Creating collection - #{collection_name}"
collection = Chroma::Resources::Collection.create(collection_name, { lang: "ruby" }) unless collection

chunks.each do |chunk|
  chunk[:embedding] = get_embedding(chunk[:content], openai)
end

# 4. Insert into Chroma
embeddings = chunks.each_with_index.map do |chunk, idx|
  Chroma::Resources::Embedding.new(
    id: "chunk-#{idx}",
    embedding: chunk[:embedding],
    metadata: chunk[:metadata],
    document: chunk[:content]
  )
end

collection.add(embeddings)
puts "Vectorstore created with #{embeddings.size} documents"

# Now 'chunks' is an array of hashes with chunk[:] and metadata.
