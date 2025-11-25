#!/usr/bin/env bash
# Bash completion script for docling-hybrid-ocr
#
# Installation:
#   # For user install:
#   mkdir -p ~/.local/share/bash-completion/completions
#   cp scripts/completion.bash ~/.local/share/bash-completion/completions/docling-hybrid-ocr
#
#   # For system-wide install:
#   sudo cp scripts/completion.bash /etc/bash_completion.d/docling-hybrid-ocr
#
# Then restart your shell or run: source ~/.bashrc

_docling_hybrid_ocr_completion() {
    local cur prev opts base
    COMPREPLY=()
    cur="${COMP_WORDS[COMP_CWORD]}"
    prev="${COMP_WORDS[COMP_CWORD-1]}"

    # Main commands
    local commands="convert convert-batch backends info health validate-config --version --help"

    # Get the main command (first non-option argument)
    local cmd=""
    for ((i=1; i<COMP_CWORD; i++)); do
        if [[ "${COMP_WORDS[i]}" != -* ]]; then
            cmd="${COMP_WORDS[i]}"
            break
        fi
    done

    # If no command yet, complete commands
    if [[ -z "$cmd" ]]; then
        COMPREPLY=( $(compgen -W "${commands}" -- "${cur}") )
        return 0
    fi

    # Command-specific completions
    case "${cmd}" in
        convert)
            case "${prev}" in
                --output|-o)
                    # Complete file names
                    COMPREPLY=( $(compgen -f -- "${cur}") )
                    return 0
                    ;;
                --backend|-b)
                    # Complete backend names
                    local backends="nemotron-openrouter deepseek-vllm deepseek-mlx"
                    COMPREPLY=( $(compgen -W "${backends}" -- "${cur}") )
                    return 0
                    ;;
                --config|-c)
                    # Complete .toml files
                    COMPREPLY=( $(compgen -f -X '!*.toml' -- "${cur}") )
                    return 0
                    ;;
                --dpi)
                    # Suggest common DPI values
                    COMPREPLY=( $(compgen -W "72 100 150 200 300" -- "${cur}") )
                    return 0
                    ;;
                --max-pages|-n|--start-page|-s)
                    # No completion for numbers
                    return 0
                    ;;
                *)
                    # If current word starts with -, complete options
                    if [[ ${cur} == -* ]]; then
                        local opts="--output -o --backend -b --config -c --dpi --max-pages -n --start-page -s --no-separators --verbose -V --help"
                        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                    else
                        # Complete PDF file names
                        COMPREPLY=( $(compgen -f -X '!*.pdf' -- "${cur}") )
                    fi
                    return 0
                    ;;
            esac
            ;;

        convert-batch)
            case "${prev}" in
                --output-dir|-o)
                    # Complete directory names
                    COMPREPLY=( $(compgen -d -- "${cur}") )
                    return 0
                    ;;
                --backend|-b)
                    local backends="nemotron-openrouter deepseek-vllm deepseek-mlx"
                    COMPREPLY=( $(compgen -W "${backends}" -- "${cur}") )
                    return 0
                    ;;
                --config|-c)
                    COMPREPLY=( $(compgen -f -X '!*.toml' -- "${cur}") )
                    return 0
                    ;;
                --parallel|-p)
                    COMPREPLY=( $(compgen -W "1 2 4 8 16" -- "${cur}") )
                    return 0
                    ;;
                --pattern)
                    COMPREPLY=( $(compgen -W "*.pdf *.PDF **/*.pdf" -- "${cur}") )
                    return 0
                    ;;
                *)
                    if [[ ${cur} == -* ]]; then
                        local opts="--output-dir -o --backend -b --config -c --parallel -p --recursive -r --pattern --dpi --max-pages -n --verbose -V --help"
                        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                    else
                        # Complete directory names for input
                        COMPREPLY=( $(compgen -d -- "${cur}") )
                    fi
                    return 0
                    ;;
            esac
            ;;

        backends)
            if [[ ${cur} == -* ]]; then
                COMPREPLY=( $(compgen -W "--help" -- "${cur}") )
            fi
            return 0
            ;;

        info)
            if [[ ${cur} == -* ]]; then
                COMPREPLY=( $(compgen -W "--help" -- "${cur}") )
            fi
            return 0
            ;;

        health)
            case "${prev}" in
                --config|-c)
                    COMPREPLY=( $(compgen -f -X '!*.toml' -- "${cur}") )
                    return 0
                    ;;
                --timeout|-t)
                    COMPREPLY=( $(compgen -W "5 10 30 60" -- "${cur}") )
                    return 0
                    ;;
                *)
                    if [[ ${cur} == -* ]]; then
                        local opts="--config -c --skip-backends --timeout -t --verbose -v --help"
                        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                    fi
                    return 0
                    ;;
            esac
            ;;

        validate-config)
            case "${prev}" in
                --config|-c)
                    COMPREPLY=( $(compgen -f -X '!*.toml' -- "${cur}") )
                    return 0
                    ;;
                *)
                    if [[ ${cur} == -* ]]; then
                        local opts="--config -c --verbose -v --help"
                        COMPREPLY=( $(compgen -W "${opts}" -- "${cur}") )
                    fi
                    return 0
                    ;;
            esac
            ;;
    esac
}

# Register the completion function
complete -F _docling_hybrid_ocr_completion docling-hybrid-ocr
