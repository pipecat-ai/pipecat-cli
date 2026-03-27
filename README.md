# Pipecat CLI

A complete toolkit for building, deploying, and monitoring [Pipecat](https://github.com/pipecat-ai/pipecat) AI voice agents.

- **Scaffold** new projects with `pipecat init`
- **Deploy** to production with `pipecat cloud`
- **Monitor** live bots with `pipecat tail`

## Requirements

- Python 3.10+

## Installation

```bash
uv tool install pipecat-ai-cli
```

This installs the CLI globally. If you don't have `uv`, you can also use `pipx install pipecat-ai-cli`.

> **Tip:** All commands can use either `pipecat` or the shorter `pc` alias.

**Optional: Install Tail Dashboard**

To use the `pipecat tail` monitoring dashboard, install with the `tail` extra:

```bash
uv tool install "pipecat-ai-cli[tail]"
```

## Create a New Project

Create a new quickstart Pipecat project with default settings:

```bash
pipecat init quickstart
```

Or create a new Pipecat project interactively:

```bash
pipecat init
```

The CLI will guide you through selecting:

- Bot type and client framework
- Transport provider (Daily, Twilio, etc.)
- Pipeline mode (Cascade or Realtime)
- AI services (STT, LLM, TTS)
- Optional features and deployment target

**Generated Project Structure**

```
mybot/
├── server/                  # Python bot server
│   ├── bot.py              # Main bot implementation
│   ├── pyproject.toml      # Python dependencies
│   ├── .env.example        # Environment variables template
│   ├── Dockerfile          # Container image (if cloud enabled)
│   └── pcc-deploy.toml     # Deployment config (if cloud enabled)
├── client/                  # Web client (if generated)
│   ├── src/
│   ├── package.json
│   └── ...
├── .gitignore
└── README.md                # Project setup instructions
```

## Deploy to Pipecat Cloud

Deploy and manage your bot in production with [Pipecat Cloud](https://www.daily.co/products/pipecat-cloud/):

```bash
# Authenticate
pipecat cloud auth login

# Deploy
pipecat cloud deploy

# Manage deployments
pipecat cloud agent list
pipecat cloud agent logs <agent-name>
```

Cloud commands provide:

- 🔐 Authentication and credential management
- 🐳 Docker build and registry integration
- 🚀 One-command deployment
- 📊 Agent status and log monitoring
- 🔧 Runtime configuration management

**Note:** When you enable "Deploy to Pipecat Cloud" during project creation, the necessary deployment config files are automatically generated.

Learn more in the [Pipecat Cloud documentation](https://docs.pipecat.ai/deployment/pipecat-cloud/introduction).

## Monitor Your Bot

Use the built-in Tail dashboard to monitor your bot in real-time:

```bash
# Connect to local bot (default: ws://localhost:9292)
pipecat tail

# Connect to remote session
pipecat tail --url wss://your-bot.example.com
```

> **Note:** The `tail` command requires the optional `tail` extra. Install with `uv tool install "pipecat-ai-cli[tail]"` if not already installed.

Tail provides:

- 📜 Real-time system logs
- 💬 Live conversation tracking
- 🔊 Audio level monitoring
- 📈 Service metrics and usage stats

## 📚 Next steps

- See the [Pipecat documentation](https://docs.pipecat.ai) for more about building bots
- Learn how to extend the template using [examples & recipes](https://docs.pipecat.ai/examples)
- [Join our Discord](https://discord.gg/pipecat) to get help or provide feedback
