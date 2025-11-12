# 🚀 Quick Start - Agent Sanitizer

## For Claude Code Users

**Turn your Claude Code logs into a shareable dataset in 3 steps:**

### Step 1: Run the Tool

```bash
uvx agent-sanitizer
```

That's it! The tool will:
- Auto-detect your `~/.claude/projects` directory
- Scan for security issues
- Show you what it found
- Ask for confirmation before cleaning

### Step 2: Review the Results

You'll see a report like:

```
Security Audit Results
┌────────────┬───────┬────────────┐
│ Category   │ Found │ Severity   │
├────────────┼───────┼────────────┤
│ Credentials│ 12    │ 🔴 Critical│
│ Names      │ 8     │ 🟡 Medium  │
│ Emails     │ 5     │ 🟡 Medium  │
└────────────┴───────┴────────────┘
```

### Step 3: Share Your Dataset

**Option A: Save Locally**
```bash
uvx agent-sanitizer --output ./my-dataset
```

**Option B: Upload to HuggingFace**
```bash
# Login first
huggingface-cli login

# Sanitize and upload
uvx agent-sanitizer --upload yourusername/my-coding-dataset
```

---

## Advanced Usage

### Dry Run First

See what would change without modifying files:

```bash
uvx agent-sanitizer --dry-run
```

### Specify Directories

```bash
uvx agent-sanitizer \
    --input ~/.claude/projects \
    --output ./clean-dataset
```

### Non-Interactive Mode

For scripts/automation:

```bash
uvx agent-sanitizer \
    --input ~/.claude/projects \
    --output ./clean-dataset \
    --no-interactive
```

---

## What Gets Cleaned

### ✅ Removed
- API keys (OpenAI, Anthropic, DeepSeek, etc.)
- Passwords and tokens
- Email addresses
- Phone numbers
- Personal names
- Cryptocurrency private keys

### ✅ Preserved
- Code examples and snippets
- Test data (Hardhat accounts, test seeds)
- Tool usage patterns
- Thinking traces
- Error handling flows
- Technical usernames

---

## Example Output

After running, you'll have:

```
clean-dataset/
├── splits/
│   ├── train.jsonl    # 80% of your data
│   ├── val.jsonl      # 10% of your data
│   └── test.jsonl     # 10% of your data
└── audit_report.json  # What was found and cleaned
```

---

## Using Your Dataset

### Load in Python

```python
from datasets import load_dataset

# If uploaded to HuggingFace
dataset = load_dataset("yourusername/my-coding-dataset")

# Or load locally
import json

with open("clean-dataset/splits/train.jsonl") as f:
    data = [json.loads(line) for line in f]

print(f"Loaded {len(data)} coding interactions!")
```

### Train a Model

Use the dataset to fine-tune your own coding assistant:

```bash
# Using transformers
python train.py \
    --dataset yourusername/my-coding-dataset \
    --model zenlm/zen-coder-14b \
    --output ./my-coding-assistant
```

---

## Troubleshooting

### "No agent logs found"

Make sure you're pointing to the right directory:

```bash
# For Claude Code
uvx agent-sanitizer --input ~/.claude/projects

# For Cursor
uvx agent-sanitizer --input ~/.cursor/logs

# For Continue
uvx agent-sanitizer --input ~/.continue/sessions
```

### "huggingface_hub not found"

Install it:

```bash
pip install huggingface_hub
```

Or use uvx with dependencies:

```bash
uvx --with huggingface_hub agent-sanitizer --upload user/dataset
```

### "Permission denied"

Login to HuggingFace first:

```bash
huggingface-cli login
```

---

## Community

Share your dataset and help grow the community!

1. **Tag it**: Add `agent-coding-dataset` tag on HuggingFace
2. **Link back**: Mention Agent Sanitizer in your dataset card
3. **Share**: Post on Twitter/X with #AgentSanitizer

**Example datasets:**
- [zenlm/agent-coding-dataset](https://huggingface.co/datasets/zenlm/agent-coding-dataset) - 161k Claude Code interactions

---

## Next Steps

- ⭐ Star the repo: https://github.com/zenlm/agent-sanitizer
- 📚 Read full docs: https://github.com/zenlm/agent-sanitizer#readme
- 🐛 Report issues: https://github.com/zenlm/agent-sanitizer/issues
- 💬 Discuss: https://github.com/zenlm/agent-sanitizer/discussions

**Happy dataset sharing! 🎉**
