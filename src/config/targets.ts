import 'dotenv/config';
import { readFileSync } from 'fs';
import { join } from 'path';
import { homedir } from 'os';

// Interface for MCP server configuration
export interface MCPServerConfig {
  command: string;
  args: string[];
  env?: Record<string, string>;
  url?: string;
  name?: string;
}

export interface MCPConfig {
  mcpServers: Record<string, MCPServerConfig>;
}

// Load MCP configuration from mcp.json file
function loadMCPConfig(): MCPConfig {
  try {
    const mcpConfigPath = join(homedir(), '.cursor', 'mcp.json');
    const configData = readFileSync(mcpConfigPath, 'utf-8');
    return JSON.parse(configData) as MCPConfig;
  } catch (error) {
    console.warn('Failed to load mcp.json, using default configuration:', error);
    return {
      mcpServers: {
        filesystem: {
          command: "docker",
          args: [
            "run",
            "-i",
            "--rm",
            "--mount", `type=bind,src=${join(homedir(), 'Documents')},dst=/project`,
            "mcp/filesystem",
            "/project"
          ]
        },
        github: {
          command: "docker",
          args: [
            "run",
            "-i",
            "--rm",
            "-e",
            "GITHUB_PERSONAL_ACCESS_TOKEN",
            "github-mcp-server"
          ],
          env: {
            "GITHUB_PERSONAL_ACCESS_TOKEN": process.env.GITHUB_PERSONAL_ACCESS_TOKEN || ""
          }
        }
      }
    };
  }
}

// Load the configuration
export const MCP_CONFIG = loadMCPConfig();

// Update filesystem config to use Documents folder properly
if (MCP_CONFIG.mcpServers.filesystem) {
  const documentsPath = join(homedir(), 'Documents');
  MCP_CONFIG.mcpServers.filesystem.args = MCP_CONFIG.mcpServers.filesystem.args.map(arg => 
    arg.includes('~/Documents') ? arg.replace('~/Documents', documentsPath) : arg
  );
}

// Export server configurations for easy access
export const SERVER_CONFIGS = MCP_CONFIG.mcpServers;

// Legacy TARGETS export for backward compatibility (using default URLs)
export const TARGETS = {
  filesystem: process.env.MCP_FILESYSTEM_URL || 'http://localhost:7001',
  github:     process.env.MCP_GITHUB_URL     || 'http://localhost:7002',
  atlassian:  process.env.MCP_ATLASSIAN_URL  || 'http://localhost:7003',
  gdrive:     process.env.MCP_GDRIVE_URL     || 'http://localhost:7004',
  playwright: process.env.MCP_PLAYWRIGHT_URL || 'http://localhost:7005'
};

export type TargetKey = keyof typeof TARGETS;
export type ServerName = keyof typeof SERVER_CONFIGS;
