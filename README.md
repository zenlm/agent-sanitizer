# 🧹 Agent Sanitizer

**Clean AI agent logs for safe dataset sharing**

Turn your Claude Code, Cursor, Continue, or Aider logs into publishable training datasets with one command.

[![PyPI](https://img.shields.io/pypi/v/agent-sanitizer)](https://pypi.org/project/agent-sanitizer/)
[![License](https://img.shields.io/badge/license-BSD--3--Clause-blue)](LICENSE)

## Quick Start

No installation required! Run with `uvx`:

```bash
# Interactive mode (recommended for first time)
uvx agent-sanitizer

# Specify input/output
uvx agent-sanitizer --input ~/.claude/projects --output ./my-dataset

# Dry run to see what would change
uvx agent-sanitizer --dry-run

# Upload directly to HuggingFace
uvx agent-sanitizer --upload username/my-dataset
```

## What It Does

Agent Sanitizer automatically removes:

- ✅ **Credentials**: API keys, passwords, tokens
- ✅ **PII**: Names, emails, phone numbers
- ✅ **Crypto**: Wallet keys, seed phrases
- ✅ **Paths**: Identifying file paths and project names

While preserving:

- ✅ **Code examples**: Including test data and development configs
- ✅ **Tool usage**: File operations, commands, workflows
- ✅ **Thinking traces**: Multi-step reasoning
- ✅ **Context**: Real coding patterns

## Supported Agents

- 🤖 **Claude Code** (`.claude/projects`)
- 🔮 **Cursor** (`.cursor/logs`)
- ⏭️ **Continue** (`.continue/sessions`)
- 🔧 **Aider** (`.aider/history`)
- 📝 **Any JSONL-based agent logs**

## Features

### 🔒 Comprehensive Security Audit

Before cleaning, scans for:
- Credentials (API keys, passwords, tokens)
- Personal information (names, emails, phones)
- Cryptocurrency (wallets, keys, seeds)
- Sensitive data (SSNs, private keys)

### 🎯 Smart Cleaning

- Pattern-based detection with low false positives
- Context-aware replacements
- Preserves test data and examples
- Maintains dataset value

### 📤 HuggingFace Integration

Upload directly after sanitization:

```bash
uvx agent-sanitizer \
    --input ~/.claude/projects \
    --upload username/my-coding-dataset \
    --private  # optional: make dataset private
```

### 🔍 Dry Run Mode

See exactly what would change:

```bash
uvx agent-sanitizer --dry-run
```

## Installation

### Option 1: Run with uvx (Recommended)

No installation needed:

```bash
uvx agent-sanitizer
```

### Option 2: Install with pip

```bash
pip install agent-sanitizer
agent-sanitizer --help
```

### Option 3: Install from source

```bash
git clone https://github.com/zenlm/agent-sanitizer
cd agent-sanitizer
pip install -e .
```

## Usage Examples

### Basic Usage

```bash
# Interactive - walks you through the process
uvx agent-sanitizer

# Specify directories
uvx agent-sanitizer \
    --input ~/.claude/projects \
    --output ./clean-dataset

# Non-interactive mode
uvx agent-sanitizer \
    --input ~/.claude/projects \
    --output ./clean-dataset \
    --no-interactive
```

### Upload to HuggingFace

```bash
# Login first
huggingface-cli login

# Sanitize and upload in one command
uvx agent-sanitizer \
    --input ~/.claude/projects \
    --upload myusername/my-coding-dataset

# Make it private
uvx agent-sanitizer \
    --input ~/.claude/projects \
    --upload myusername/my-dataset \
    --private
```

### Use Sanitized Dataset

After sanitization, use the dataset:

```python
from datasets import load_dataset

# If uploaded to HuggingFace
dataset = load_dataset("username/my-coding-dataset")

# Or load from local directory
import json

data = []
with open("clean-dataset/splits/train.jsonl") as f:
    for line in f:
        data.append(json.loads(line))

print(f"Loaded {len(data)} examples")
```

## Output Format

Creates a structured dataset:

```
clean-dataset/
├── splits/
│   ├── train.jsonl
│   ├── val.jsonl
│   └── test.jsonl
├── audit_report.json
└── sanitization_summary.json
```

Each JSONL line contains:
- `timestamp`: When the interaction occurred
- `model`: Which AI model was used
- `tokens`: Token usage breakdown
- `content`: Array of content blocks (thinking, tool use, text)
- `cwd`: Working directory (anonymized)
- `git_branch`: Git context

## Security

### What Gets Removed

1. **Credentials**
   - API keys (OpenAI, Anthropic, etc.)
   - Passwords and auth tokens
   - GitHub personal access tokens
   - SSH/PGP private keys

2. **Personal Information**
   - Email addresses (except safe ones like user@example.com)
   - Phone numbers
   - SSNs
   - Personal names

3. **Cryptocurrency**
   - Private keys (Ethereum, Bitcoin, etc.)
   - Seed phrases
   - Wallet addresses (when not test data)

### What Gets Preserved

1. **Test Data**
   - Hardhat/Ganache test accounts
   - BIP-39 test seed phrases
   - Localhost configurations

2. **Examples**
   - Code snippets with placeholders
   - Documentation
   - Tutorial content

3. **Technical Context**
   - Usernames (demonstrates workflows)
   - Tool usage patterns
   - Error handling flows

## Contributing

Contributions welcome! Please:

1. Check existing issues
2. Create feature branch
3. Add tests for new patterns
4. Submit pull request

## Community Datasets

Share your sanitized dataset:

1. Upload to HuggingFace with `--upload`
2. Tag with `agent-coding-dataset`
3. Link to original tool in dataset card

Example datasets:
- [zenlm/agent-coding-dataset](https://huggingface.co/datasets/zenlm/agent-coding-dataset) - 161k Claude Code interactions

## License

BSD-3-Clause - See [LICENSE](LICENSE)

## Links

- **GitHub**: https://github.com/zenlm/agent-sanitizer
- **PyPI**: https://pypi.org/project/agent-sanitizer/
- **Example Dataset**: https://huggingface.co/datasets/zenlm/agent-coding-dataset
- **Issues**: https://github.com/zenlm/agent-sanitizer/issues

## Acknowledgments

Built by [Zen AI](https://zenlm.org) to help the community share coding datasets safely.

---

**Made with ❤️ for the AI coding community**
