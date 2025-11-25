# Shell Completion Scripts

This directory contains shell completion scripts for `docling-hybrid-ocr` to provide tab completion for commands, options, and file paths.

## Available Completions

- `completion.bash` - Bash completion script
- `completion.zsh` - Zsh completion script

## Installation

### Bash

#### User Installation (Recommended)

```bash
# Create completion directory if it doesn't exist
mkdir -p ~/.local/share/bash-completion/completions

# Copy the completion script
cp scripts/completion.bash ~/.local/share/bash-completion/completions/docling-hybrid-ocr

# Restart your shell or reload
source ~/.bashrc
```

#### System-wide Installation

```bash
# Install for all users (requires sudo)
sudo cp scripts/completion.bash /etc/bash_completion.d/docling-hybrid-ocr

# Restart your shell or reload
source /etc/bash_completion
```

### Zsh

#### User Installation (Recommended)

```bash
# Create completion directory if it doesn't exist
mkdir -p ~/.zsh/completion

# Copy the completion script
cp scripts/completion.zsh ~/.zsh/completion/_docling-hybrid-ocr

# Add to your ~/.zshrc if not already present:
echo 'fpath=(~/.zsh/completion $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc

# Restart your shell or reload
source ~/.zshrc
```

#### Alternative (Using Scripts Directory)

```bash
# Add to your ~/.zshrc:
fpath=(~/path/to/pdfz/scripts $fpath)
autoload -U compinit && compinit
```

## Usage

Once installed, tab completion will work for:

### Commands
```bash
docling-hybrid-ocr <TAB>
# Shows: convert  convert-batch  backends  info  health  validate-config  --version  --help
```

### Options
```bash
docling-hybrid-ocr convert --<TAB>
# Shows: --output  --backend  --config  --dpi  --max-pages  --start-page  --no-separators  --verbose  --help
```

### Files
```bash
docling-hybrid-ocr convert <TAB>
# Auto-completes .pdf files in current directory

docling-hybrid-ocr convert document.pdf --output <TAB>
# Auto-completes file paths for output
```

### Backend Names
```bash
docling-hybrid-ocr convert document.pdf --backend <TAB>
# Shows: nemotron-openrouter  deepseek-vllm  deepseek-mlx
```

### Config Files
```bash
docling-hybrid-ocr convert document.pdf --config <TAB>
# Auto-completes .toml files
```

## Features

The completion scripts provide intelligent completion for:

- **Commands**: All main commands (convert, convert-batch, backends, info, health, validate-config)
- **Options**: Command-specific options with short and long forms
- **File paths**: Context-aware file completion (PDF files for input, directories for output)
- **Backend names**: Suggests available backends
- **Configuration files**: Completes .toml configuration files
- **Common values**: Suggests common values for DPI, parallelism, timeouts, etc.

## Testing

To test if completion is working:

```bash
# Type this and press TAB:
docling-hybrid-ocr <TAB>

# Should show available commands

# Type this and press TAB:
docling-hybrid-ocr convert --<TAB>

# Should show available options
```

## Troubleshooting

### Bash completion not working

1. Check if bash-completion is installed:
   ```bash
   # On Ubuntu/Debian:
   sudo apt install bash-completion

   # On macOS with Homebrew:
   brew install bash-completion@2
   ```

2. Ensure completion is sourced in your `~/.bashrc`:
   ```bash
   if [ -f /etc/bash_completion ]; then
       . /etc/bash_completion
   fi
   ```

3. Reload your shell configuration:
   ```bash
   source ~/.bashrc
   ```

### Zsh completion not working

1. Make sure the fpath is set before compinit:
   ```zsh
   # In ~/.zshrc
   fpath=(~/.zsh/completion $fpath)
   autoload -U compinit && compinit
   ```

2. Clear the completion cache:
   ```bash
   rm -f ~/.zcompdump
   exec zsh
   ```

3. Check if compinit is being called:
   ```bash
   which compinit
   ```

## Updating Completions

If you update the CLI commands or options, remember to:

1. Update both `completion.bash` and `completion.zsh`
2. Test the completions after changes
3. Document any new features in this README

## Contributing

When adding new commands or options to the CLI:

1. Add completion support in both scripts
2. Test with both bash and zsh
3. Update this documentation
