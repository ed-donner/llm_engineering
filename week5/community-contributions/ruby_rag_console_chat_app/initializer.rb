require 'pathname'
require 'pry'
require 'openai'
require "ruby-next/language/runtime"
require 'chroma-db'
require 'logger'
require 'json'

Chroma.connect_host = "http://localhost:8000"
Chroma.api_version = "v2"
Chroma.logger = Logger.new($stdout)
Chroma.log_level = Chroma::LEVEL_ERROR