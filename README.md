# OpenRouter Skills

A collection of Agent Skills for building with OpenRouter, a unified API for hundreds of AI models.

## Installing

These skills work with agents that support the Agent Skills standard, including Claude Code, Cursor, OpenCode, OpenAI Codex, and Pi.

For agents that support plugins, installing through the native plugin system is recommended because skills can update automatically.

### Claude Code

```
/plugin marketplace add OpenRouterTeam/skills
/plugin install openrouter@openrouter
```

### Cursor

Add a remote rule from `OpenRouterTeam/skills` in Cursor settings.

### OpenCode

```bash
git clone https://github.com/OpenRouterTeam/skills.git /tmp/openrouter-skills
cp -r /tmp/openrouter-skills/skills/* ~/.config/opencode/skills/
rm -rf /tmp/openrouter-skills
```

### GitHub CLI

```bash
gh skill install OpenRouterTeam/skills
```

Install one skill by name:

```bash
gh skill install OpenRouterTeam/skills openrouter-images
```

Use `--scope user` to install for the current agent account or `--agent claude-code` to target a specific agent.

## Skills

| Skill | Useful for |
|-------|------------|
| [create-agent-tui](skills/create-agent-tui/README.md) | Scaffolds a complete Python agent TUI with input styles, tool display modes, banners, loaders, session persistence, and local tools. |
| [create-headless-agent](skills/create-headless-agent/README.md) | Scaffolds a headless Python agent for CLI tools, API services, queue workers, and pipelines. |
| [openrouter-python-sdk](skills/openrouter-python-sdk/README.md) | Complete Python reference for OpenRouter chat, Responses, streaming, tool calling, and model metadata. |
| [openrouter-agent-migration](skills/openrouter-agent-migration/README.md) | Converts older OpenRouter agent examples to Python using the OpenRouter SDK or low-level Responses API requests. |
| [openrouter-models](skills/openrouter-models/README.md) | Querying available models, comparing pricing, checking context lengths, and resolving model names. |
| [openrouter-images](skills/openrouter-images/README.md) | Generating and editing images with OpenRouter image models from Python. |
| [openrouter-oauth](skills/openrouter-oauth/README.md) | Sign in with OpenRouter using OAuth PKCE and Python server callbacks. |
| [openrouter-stt](skills/openrouter-stt/README.md) | Speech-to-text transcription through OpenRouter. |
| [openrouter-tts](skills/openrouter-tts/README.md) | Text-to-speech generation through OpenRouter. |
| [openrouter-video](skills/openrouter-video/README.md) | Video generation workflows through OpenRouter. |

## Environment

Most examples read `OPENROUTER_API_KEY` from the environment. Get a key at [openrouter.ai/keys](https://openrouter.ai/keys).

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Python SDK](https://openrouter.ai/docs/client-sdks/python/overview)
- [OpenRouter Models](https://openrouter.ai/models)
