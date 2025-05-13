// Import Gmail adapter
import { getGmailService, getEmailBody, getOrCreateLabel } from './gmailAdapter.js';
import { google } from 'googleapis';
import time from 'node:timers/promises';
import json from 'node:fs';
import { get_llm } from './tools.js';
import { ChatPromptTemplate } from 'langchain/prompts';
import { StrOutputParser } from 'langchain/schema/output_parser';

// Initialize Gmail service with access token from global space
let service; 