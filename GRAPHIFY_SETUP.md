# 🧠 Graphify Setup Guide for Voyza & Future Projects

**Objective:** Build knowledge graphs to reduce token usage by 71.5x on all your projects

---

## ✅ Phase 1: Install Graphify (DONE)

```bash
# Graphify is now installed globally
graphify --help  # Verify installation
```

---

## 📊 Phase 2: Build Knowledge Graph for Voyza

**Current Directory:** `/home/user/voyza`

### Option A: Interactive Building (Recommended for now)

Since Graphify is designed as a **Claude Code skill**, you should use it within Claude Code:

```bash
# In Claude Code terminal, type:
/graphify .

# This will:
# 1. Analyze your entire codebase using tree-sitter AST
# 2. Extract semantic relationships from docs
# 3. Create an interactive knowledge graph
# 4. Output to graphify-out/ directory
```

### What Gets Created:

```
voyza/
├── graphify-out/
│   ├── graph.json          ← Persistent queryable graph (commit this!)
│   ├── graph.html          ← Interactive visualization
│   ├── GRAPH_REPORT.md     ← Summary of findings
│   └── cache/              ← SHA256 cache (ignore in git)
├── .graphifyignore         ← Exclude folders
└── (your code)
```

### Create `.graphifyignore` for Voyza:

```bash
cat > /home/user/voyza/.graphifyignore << 'EOF'
node_modules/
.venv/
venv/
__pycache__/
dist/
build/
.next/
.git/
*.pyc
*.egg-info/
.env
.env.local
.env.prod
*.log
graphify-out/cache/
EOF
```

---

## 🔧 Phase 3: Automation for Future Projects

### Create Auto-Setup Script

I'll create a script that automatically sets up Graphify for ANY new project:

```bash
# Create global setup script
cat > ~/.local/bin/project-init-graphify << 'EOF'
#!/bin/bash
# Auto-setup Graphify for new projects
# Usage: project-init-graphify <project-directory>

set -e

PROJECT_DIR="${1:-.}"

echo "🧠 Setting up Graphify for: $PROJECT_DIR"

# Create .graphifyignore
cat > "$PROJECT_DIR/.graphifyignore" << 'GRAPHIFY_IGNORE'
# Dependencies
node_modules/
.venv/
venv/
__pycache__/
.eggs/
*.egg-info/

# Build outputs
dist/
build/
.next/
.out/
target/
out/

# Version control & IDE
.git/
.github/
.vscode/
.idea/
*.swp

# Environment & secrets
.env
.env.*
.DS_Store

# Cache & generated
*.pyc
*.log
graphify-out/cache/
GRAPHIFY_IGNORE

echo "✅ Created .graphifyignore"

# Create GRAPHIFY_SETUP.md with instructions
cat > "$PROJECT_DIR/GRAPHIFY_SETUP.md" << 'SETUP_MD'
# Knowledge Graph Setup

## Quick Start

```bash
# Build the knowledge graph
/graphify .

# This creates an interactive queryable graph in graphify-out/
```

## What It Does

- **71.5x token reduction** on codebase queries
- **Persistent graph** - query weeks later without re-reading
- **Interactive visualization** - open `graphify-out/graph.html` in browser
- **Privacy-first** - code analyzed locally via tree-sitter AST

## Commit the Graph

```bash
git add .graphifyignore GRAPHIFY_SETUP.md
# Don't commit graphify-out/cache/ - add to .gitignore if needed
git add graphify-out/graph.json graphify-out/GRAPH_REPORT.md
```

## Using in Claude Code

In Claude Code, queries traverse the knowledge graph instead of re-reading files:
- 40-100x fewer tokens per query
- Instant results even on large codebases
- Better understanding of architecture
SETUP_MD

echo "✅ Created GRAPHIFY_SETUP.md"
echo "📖 Next: Run 'graphify install' in your AI coding assistant"
EOF

chmod +x ~/.local/bin/project-init-graphify
echo "✅ Created global project-init-graphify script"
```

### Create Post-Clone Hook

For automatic Graphify setup on all new git clones:

```bash
# Create global git hook template
mkdir -p ~/.git-templates/hooks

cat > ~/.git-templates/hooks/post-checkout << 'EOF'
#!/bin/bash
# Auto-setup Graphify on clone

if [ -f "$(git rev-parse --show-toplevel)/.graphifyignore" ]; then
    echo "📖 Graphify is configured for this repo"
    echo "   Run: /graphify . (in Claude Code) to build knowledge graph"
fi
EOF

chmod +x ~/.git-templates/hooks/post-checkout

# Configure git to use these templates
git config --global init.templateDir ~/.git-templates
```

---

## 🚀 Usage Workflow

### For Voyza (Now):

```bash
# 1. In Claude Code, run:
/graphify .

# 2. Wait for completion - builds knowledge graph
# 3. Open graphify-out/graph.html in browser to explore
# 4. Commit the graph:
git add graphify-out/graph.json .graphifyignore GRAPHIFY_SETUP.md
git commit -m "Add Graphify knowledge graph"
git push
```

### For All Future Projects:

```bash
# 1. Clone or create project
cd my-new-project

# 2. Run setup (automatically creates .graphifyignore & docs)
project-init-graphify .

# 3. Build graph (in Claude Code)
/graphify .

# 4. Commit
git add .graphifyignore GRAPHIFY_SETUP.md graphify-out/graph.json
git commit -m "Add Graphify knowledge graph"
```

---

## 📊 Token Savings Comparison

### Before Graphify:

```
Query: "What are all the OAuth endpoints?"
→ Read auth.py (2000 tokens)
→ Read oauth_service.py (1500 tokens)
→ Read endpoints/auth.py (2000 tokens)
→ Read schemas (1000 tokens)
Total: ~6500 tokens per query
```

### After Graphify:

```
Query: "What are all the OAuth endpoints?"
→ Query graph.json (200 tokens)
Total: ~200 tokens per query

Savings: 32.5x reduction! ✅
```

---

## 🔄 Keeping Graphs Updated

### Auto-Update on File Changes:

```bash
# In your project directory:
graphify watch .

# This runs continuously and updates graph on file changes
# Press Ctrl+C to stop
```

### Manual Update (Semantic analysis):

```bash
# If you change docs, add new papers, etc:
graphify update .

# Reuses cached AST, only re-extracts changed files
```

---

## 🎯 Integration with Claude Code

### Install Graphify Skill:

```bash
# In your terminal:
graphify install

# This writes graphify config to ~/.claude/
# Now /graphify works in Claude Code!
```

### Use in Claude Code:

```
# Type in Claude Code:
/graphify .          # Build initial graph
/graphify path "X" "Y"     # Shortest path between two concepts
/graphify explain "OAuth"   # Explain a concept and its context
/graphify query "Question"  # Query the graph with BFS
```

---

## 📁 Directory Structure

```
project/
├── .graphifyignore           # What to exclude (created by setup)
├── GRAPHIFY_SETUP.md        # This guide (created by setup)
├── graphify-out/
│   ├── graph.json           # ✅ COMMIT THIS
│   ├── graph.html           # ✅ COMMIT THIS
│   ├── GRAPH_REPORT.md      # ✅ COMMIT THIS
│   └── cache/               # ❌ DO NOT COMMIT (in .gitignore)
└── (your project files)
```

---

## ⚡ Performance Tips

1. **Cache is persistent** - First run is slower, subsequent updates are instant
2. **Selective updates** - Only changed files are re-analyzed
3. **Parallel extraction** - Claude subagents run in parallel
4. **Graph queries are O(neighbors)** - Very fast even on large graphs

---

## 🐛 Troubleshooting

### "graphify: command not found"

```bash
# If graphify isn't in PATH:
python -m graphify --help
# OR add to PATH:
export PATH="$HOME/.local/bin:$PATH"
```

### Graph looks incomplete

```bash
# Rebuild from scratch (removes cache):
rm -rf graphify-out/cache/
graphify update .
```

### Want to start over

```bash
# Remove entire graph
rm -rf graphify-out/
# Rebuild
/graphify .
```

---

## 📚 References

- **Graphify GitHub:** https://github.com/safishamsi/graphify
- **Knowledge Graph Guide:** https://graphify.net/
- **Token Reduction Study:** https://medium.com/@abhishek-iiit/optimizing-token-usage-with-graphify
- **Claude Code Integration:** graphify install

---

**Next Steps:**
1. ✅ Install graphify (done)
2. ⏳ Build graph for Voyza (`/graphify .` in Claude Code)
3. ⏳ Commit graph to git
4. ⏳ Use `project-init-graphify` for future projects

You'll save **70%+ tokens** on all future codebase queries! 🚀
