import 'dotenv/config';

export const TARGETS = {
  filesystem: process.env.MCP_FILESYSTEM_URL || 'http://localhost:7001',
  github:     process.env.MCP_GITHUB_URL     || 'http://localhost:7002',
  atlassian:  process.env.MCP_ATLASSIAN_URL  || 'http://localhost:7003',
  gdrive:     process.env.MCP_GDRIVE_URL     || 'http://localhost:7004'
};

export type TargetKey = keyof typeof TARGETS;
