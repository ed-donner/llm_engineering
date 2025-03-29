"""Test module for Lua language detection."""

import sys
import os

# Add the src directory to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ai_code_converter.core.language_detection import LanguageDetector


def test_lua_detection():
    """Test the Lua language detection functionality."""
    detector = LanguageDetector()
    
    # Sample Lua code
    lua_code = """
-- Simple Lua script
local function factorial(n)
    if n == 0 then
        return 1
    else
        return n * factorial(n - 1)
    end
end

-- Variables
local name = "John"
local age = 30
local is_active = true
local value = nil

-- Table creation
local person = {
    name = "John",
    age = 30,
    email = "john@example.com",
    greet = function(self)
        return "Hello, " .. self.name
    end
}

-- Accessing table properties
print(person.name)
print(person["age"])
print(person:greet())

-- Metatables
local mt = {
    __add = function(a, b)
        return { value = a.value + b.value }
    end
}

local obj1 = { value = 10 }
local obj2 = { value = 20 }
setmetatable(obj1, mt)
local result = obj1 + obj2
print(result.value)  -- 30

-- Control structures
for i = 1, 10 do
    print(i)
end

local fruits = {"apple", "banana", "orange"}
for i, fruit in ipairs(fruits) do
    print(i, fruit)
end

for key, value in pairs(person) do
    if type(value) ~= "function" then
        print(key, value)
    end
end

local count = 1
while count <= 5 do
    print(count)
    count = count + 1
end

-- Using modules
local math = require("math")
print(math.floor(3.14))
print(math.random())

-- String operations
local message = "Hello, " .. name .. "!"
print(message)
print(string.upper(message))
print(string.sub(message, 1, 5))
print(string.find(message, "Hello"))

-- Multiple return values
local function get_person()
    return "John", 30, true
end

local name, age, active = get_person()
print(name, age, active)

-- Closures
local function counter()
    local count = 0
    return function()
        count = count + 1
        return count
    end
end

local c1 = counter()
print(c1())  -- 1
print(c1())  -- 2

-- Error handling
local status, err = pcall(function()
    error("Something went wrong")
end)

if not status then
    print("Error:", err)
end

-- Coroutines
local co = coroutine.create(function()
    for i = 1, 3 do
        print("Coroutine", i)
        coroutine.yield()
    end
end)

coroutine.resume(co)  -- Coroutine 1
coroutine.resume(co)  -- Coroutine 2
coroutine.resume(co)  -- Coroutine 3

-- Multi-line strings
local multi_line = [[
This is a multi-line
string in Lua.
It can contain "quotes" without escaping.
]]
print(multi_line)

-- Bit operations (Lua 5.3+)
local a = 10  -- 1010 in binary
local b = 6   -- 0110 in binary
print(a & b)  -- AND: 0010 = 2
print(a | b)  -- OR: 1110 = 14
print(a ~ b)  -- XOR: 1100 = 12
"""
    
    # Test the detection
    assert detector.detect_lua(lua_code) == True
    assert detector.detect_language(lua_code) == "Lua"
    
    # Check validation
    valid, _ = detector.validate_language(lua_code, "Lua")
    assert valid == True


if __name__ == "__main__":
    test_lua_detection()
    print("All Lua detection tests passed!")
