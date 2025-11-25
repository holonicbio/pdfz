#compdef docling-hybrid-ocr
# Zsh completion script for docling-hybrid-ocr
#
# Installation:
#   # Add to your ~/.zshrc:
#   fpath=(~/path/to/pdfz/scripts $fpath)
#   autoload -U compinit && compinit
#
#   # Or copy to a standard completion directory:
#   mkdir -p ~/.zsh/completion
#   cp scripts/completion.zsh ~/.zsh/completion/_docling-hybrid-ocr
#   # Then add to ~/.zshrc:
#   fpath=(~/.zsh/completion $fpath)
#   autoload -U compinit && compinit

_docling_hybrid_ocr() {
    local -a commands
    commands=(
        'convert:Convert a PDF file to Markdown'
        'convert-batch:Convert multiple PDF files in batch mode'
        'backends:List available OCR/VLM backends'
        'info:Show system information and configuration'
        'health:Check system health and backend connectivity'
        'validate-config:Validate configuration file'
    )

    local -a global_opts
    global_opts=(
        '(- :)--version[Show version and exit]'
        '(- :)--help[Show help and exit]'
    )

    _arguments -C \
        $global_opts \
        '1: :->command' \
        '*:: :->args'

    case $state in
        command)
            _describe 'command' commands
            ;;
        args)
            case $words[1] in
                convert)
                    _arguments \
                        '1:PDF file:_files -g "*.pdf"' \
                        '(-o --output)'{-o,--output}'[Output Markdown file path]:output file:_files' \
                        '(-b --backend)'{-b,--backend}'[Backend to use]:backend:(nemotron-openrouter deepseek-vllm deepseek-mlx)' \
                        '(-c --config)'{-c,--config}'[Path to configuration file]:config file:_files -g "*.toml"' \
                        '--dpi[Page rendering DPI]:dpi:(72 100 150 200 300)' \
                        '(-n --max-pages)'{-n,--max-pages}'[Maximum pages to process]:pages:' \
                        '(-s --start-page)'{-s,--start-page}'[First page to process]:page:' \
                        '--no-separators[Do not add page separator comments]' \
                        '(-V --verbose)'{-V,--verbose}'[Enable verbose logging]' \
                        '(- :)--help[Show help]'
                    ;;
                convert-batch)
                    _arguments \
                        '1:input directory:_directories' \
                        '(-o --output-dir)'{-o,--output-dir}'[Output directory]:output dir:_directories' \
                        '(-b --backend)'{-b,--backend}'[Backend to use]:backend:(nemotron-openrouter deepseek-vllm deepseek-mlx)' \
                        '(-c --config)'{-c,--config}'[Path to configuration file]:config file:_files -g "*.toml"' \
                        '(-p --parallel)'{-p,--parallel}'[Number of files to process in parallel]:workers:(1 2 4 8 16)' \
                        '(-r --recursive)'{-r,--recursive}'[Search for PDFs recursively]' \
                        '--pattern[Glob pattern for matching PDF files]:pattern:(*.pdf *.PDF **/*.pdf)' \
                        '--dpi[Page rendering DPI]:dpi:(72 100 150 200 300)' \
                        '(-n --max-pages)'{-n,--max-pages}'[Maximum pages per file]:pages:' \
                        '(-V --verbose)'{-V,--verbose}'[Enable verbose logging]' \
                        '(- :)--help[Show help]'
                    ;;
                backends)
                    _arguments \
                        '(- :)--help[Show help]'
                    ;;
                info)
                    _arguments \
                        '(- :)--help[Show help]'
                    ;;
                health)
                    _arguments \
                        '(-c --config)'{-c,--config}'[Path to configuration file]:config file:_files -g "*.toml"' \
                        '--skip-backends[Skip backend connectivity checks]' \
                        '(-t --timeout)'{-t,--timeout}'[Backend check timeout in seconds]:timeout:(5 10 30 60)' \
                        '(-v --verbose)'{-v,--verbose}'[Show detailed health information]' \
                        '(- :)--help[Show help]'
                    ;;
                validate-config)
                    _arguments \
                        '(-c --config)'{-c,--config}'[Path to configuration file]:config file:_files -g "*.toml"' \
                        '(-v --verbose)'{-v,--verbose}'[Show detailed validation information]' \
                        '(- :)--help[Show help]'
                    ;;
            esac
            ;;
    esac
}

_docling_hybrid_ocr "$@"
