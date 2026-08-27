// Day 1: Playwright Scraper - Abdennour
// scrape the website text content and pass it to OpenAI API 
import { chromium } from 'playwright';
import OpenAI from 'openai';
import dotenv from 'dotenv'; 
// Pass Screenshot to OpenAI API using OpenAI API Key from .env file
dotenv.config({path: '../../../.env'});
const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  throw new Error('OPENAI_API_KEY is not set');
}
// browserType.launch: Executable doesn't exist at ~/Library/Caches/ms-playwright/chromium_headless_shell-1200/chrome-headless-shell-mac-arm64/chrome-headless-shell
// run the following command to install the executable
// npx playwright install chromium
// or run the following command to install the executable
// npx playwright install chromium --force
// or run the following command to install the executable
// url as argument
const url = process.argv[2];
if (!url) {
  throw new Error('URL is not set - use 1st argument to set the URL');
}
const categories = ['news', 'sports', 'weather', 'entertainment', 'technology', 'science', 'health', 'finance', 'politics', 'business', 'education', 'travel', 'food', 'fashion', 'art', 'music', 'movies', 'books', 'games', 'other'];
const randomCategory = categories[Math.floor(Math.random() * categories.length)];
// parse content of the website by url using playwright
const browser = await chromium.launch();
const page = await browser.newPage();
await page.goto(url);
let content = await page.content();
await browser.close();
// for content, it must not exceed 12800 tokens
if (content.length > 12800) {
  // we need to truncate the content to 128000 tokens
  content = content.slice(0, 12800);
}
// System prompt for the OpenAI API
const system_prompt = "You are a helpful assistant that categorizes the website into a specific category based on the text content of a website.";
// User prompt for the OpenAI API
const user_prompt = `Categorize the website into a specific category based on the text content of the website: ${content}`;


const openai = new OpenAI({
  apiKey: apiKey,
});

const response = await openai.chat.completions.create({
  model: 'gpt-4o-mini',
  messages: [
    { role: 'system', content: system_prompt },
    { role: 'user', content: user_prompt },
  ],
});

console.log(response.choices[0].message.content);