#!/usr/bin/env python3
"""
Custom Backend Configuration Example

This example demonstrates how to use different OCR backends and create
custom backend configurations.

Examples shown:
1. Using a specific backend from config
2. Creating a custom backend configuration programmatically
3. Switching between backends
4. Using a local vLLM server
5. Creating a custom backend implementation (advanced)

Usage:
    # Use default backend
    python examples/custom_backend.py document.pdf

    # Use specific backend
    python examples/custom_backend.py document.pdf --backend deepseek-vllm

    # Use custom endpoint
    python examples/custom_backend.py document.pdf --custom-endpoint http://localhost:8000

Requirements:
    - OPENROUTER_API_KEY for OpenRouter backends
    - Local vLLM server for local backends
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Any

from docling_hybrid import init_config, get_config, HybridPipeline
from docling_hybrid.backends import make_backend, list_backends
from docling_hybrid.backends.base import OcrVlmBackend
from docling_hybrid.common.errors import DoclingHybridError
from docling_hybrid.common.models import OcrBackendConfig


# =============================================================================
# Example 1: Using Pre-configured Backends
# =============================================================================

async def example_preconfigured_backend(pdf_path: Path, backend_name: str) -> None:
    """
    Use a backend that's already configured in the config file.

    Args:
        pdf_path: Path to PDF file
        backend_name: Name of backend from config
    """
    print(f"\n{'='*60}")
    print("Example 1: Using Pre-configured Backend")
    print(f"{'='*60}")

    # Initialize config
    config = init_config()

    # List available backends
    backends = list_backends()
    print(f"\nAvailable backends: {backends}")

    # Get backend config
    try:
        backend_config = config.backends.get_backend_config(backend_name)
        print(f"\nUsing backend: {backend_name}")
        print(f"  Model: {backend_config.model}")
        print(f"  Endpoint: {backend_config.base_url}")
        print(f"  Temperature: {backend_config.temperature}")
        print(f"  Max tokens: {backend_config.max_tokens}")
    except KeyError:
        print(f"\n❌ Backend '{backend_name}' not found in config")
        print(f"   Available: {backends}")
        sys.exit(1)

    # Create backend
    backend = make_backend(backend_config)

    # Create pipeline with this backend
    pipeline = HybridPipeline(config, backend=backend)

    # Convert
    print(f"\n🚀 Converting {pdf_path.name}...")
    result = await pipeline.convert_pdf(pdf_path)

    print(f"\n✅ Success!")
    print(f"   Pages: {result.processed_pages}")
    print(f"   Backend: {result.backend_name}")
    print(f"   Content length: {len(result.markdown)} chars")


# =============================================================================
# Example 2: Custom Backend Configuration
# =============================================================================

async def example_custom_config(pdf_path: Path, endpoint: str) -> None:
    """
    Create a custom backend configuration programmatically.

    Args:
        pdf_path: Path to PDF file
        endpoint: Custom endpoint URL
    """
    print(f"\n{'='*60}")
    print("Example 2: Custom Backend Configuration")
    print(f"{'='*60}")

    # Initialize config
    config = init_config()

    # Create custom backend config
    custom_config = OcrBackendConfig(
        name="custom-backend",
        model="deepseek-ai/DeepSeek-OCR",
        base_url=endpoint,
        api_key=None,  # Local server, no API key needed
        temperature=0.0,
        max_tokens=8192,
    )

    print(f"\nCustom backend configuration:")
    print(f"  Name: {custom_config.name}")
    print(f"  Model: {custom_config.model}")
    print(f"  Endpoint: {custom_config.base_url}")

    # Create backend
    backend = make_backend(custom_config)

    # Create pipeline
    pipeline = HybridPipeline(config, backend=backend)

    # Convert
    print(f"\n🚀 Converting {pdf_path.name}...")
    result = await pipeline.convert_pdf(pdf_path)

    print(f"\n✅ Success!")
    print(f"   Pages: {result.processed_pages}")
    print(f"   Backend: {result.backend_name}")


# =============================================================================
# Example 3: OpenRouter with Custom Model
# =============================================================================

async def example_openrouter_custom_model(
    pdf_path: Path,
    model: str = "nvidia/nemotron-nano-12b-v2-vl:free"
) -> None:
    """
    Use OpenRouter with a custom model.

    Args:
        pdf_path: Path to PDF file
        model: OpenRouter model name
    """
    print(f"\n{'='*60}")
    print("Example 3: OpenRouter with Custom Model")
    print(f"{'='*60}")

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("\n❌ OPENROUTER_API_KEY environment variable not set")
        sys.exit(1)

    # Initialize config
    config = init_config()

    # Create custom OpenRouter config
    custom_config = OcrBackendConfig(
        name="custom-openrouter",
        model=model,
        base_url="https://openrouter.ai/api/v1/chat/completions",
        api_key=api_key,
        temperature=0.0,
        max_tokens=8192,
    )

    print(f"\nOpenRouter configuration:")
    print(f"  Model: {custom_config.model}")
    print(f"  API key: {api_key[:10]}...")

    # Create backend
    backend = make_backend(custom_config)

    # Create pipeline
    pipeline = HybridPipeline(config, backend=backend)

    # Convert
    print(f"\n🚀 Converting {pdf_path.name}...")
    result = await pipeline.convert_pdf(pdf_path)

    print(f"\n✅ Success!")
    print(f"   Pages: {result.processed_pages}")
    print(f"   Backend: {result.backend_name}")


# =============================================================================
# Example 4: Local vLLM Server
# =============================================================================

async def example_local_vllm(pdf_path: Path, vllm_endpoint: str) -> None:
    """
    Use a local vLLM server for inference.

    Args:
        pdf_path: Path to PDF file
        vllm_endpoint: vLLM server endpoint (e.g., http://localhost:8000)
    """
    print(f"\n{'='*60}")
    print("Example 4: Local vLLM Server")
    print(f"{'='*60}")

    # Initialize config
    config = init_config()

    # Create vLLM backend config
    vllm_config = OcrBackendConfig(
        name="local-vllm",
        model="deepseek-ai/DeepSeek-OCR",
        base_url=f"{vllm_endpoint}/v1/chat/completions",
        api_key=None,  # Local server, no API key
        temperature=0.0,
        max_tokens=8192,
    )

    print(f"\nvLLM configuration:")
    print(f"  Endpoint: {vllm_config.base_url}")
    print(f"  Model: {vllm_config.model}")

    # Create backend
    backend = make_backend(vllm_config)

    # Test connection
    print(f"\n🔍 Testing connection to vLLM server...")
    try:
        async with backend:
            print("   ✓ Connection successful")
    except Exception as e:
        print(f"   ✗ Connection failed: {e}")
        print("\nMake sure vLLM server is running:")
        print("  python -m vllm.entrypoints.openai.api_server \\")
        print("    --model deepseek-ai/DeepSeek-OCR \\")
        print("    --host 0.0.0.0 \\")
        print("    --port 8000")
        sys.exit(1)

    # Create pipeline
    pipeline = HybridPipeline(config, backend=backend)

    # Convert
    print(f"\n🚀 Converting {pdf_path.name}...")
    result = await pipeline.convert_pdf(pdf_path)

    print(f"\n✅ Success!")
    print(f"   Pages: {result.processed_pages}")
    print(f"   Backend: {result.backend_name}")


# =============================================================================
# Example 5: Custom Backend Implementation (Advanced)
# =============================================================================

class MockBackend(OcrVlmBackend):
    """
    A mock backend for testing (doesn't call any external API).

    This is an example of creating a custom backend implementation.
    Real backends would make API calls to VLM services.
    """

    def __init__(self, config: OcrBackendConfig) -> None:
        """Initialize mock backend."""
        self.config = config
        self.name = "mock-backend"
        print(f"   Created MockBackend: {self.name}")

    async def __aenter__(self) -> "MockBackend":
        """Enter async context manager."""
        print(f"   MockBackend: Connected")
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context manager."""
        print(f"   MockBackend: Disconnected")

    async def page_to_markdown(
        self,
        image_bytes: bytes,
        page_num: int,
        doc_id: str
    ) -> str:
        """Mock page to markdown conversion."""
        print(f"   MockBackend: Converting page {page_num} (doc: {doc_id})")

        # Return mock markdown
        return f"""# Mock Page {page_num}

This is a mock conversion result for page {page_num}.

## Document Information
- Document ID: {doc_id}
- Image size: {len(image_bytes)} bytes
- Backend: {self.name}

## Sample Table

| Column 1 | Column 2 | Column 3 |
|----------|----------|----------|
| Value 1  | Value 2  | Value 3  |
| Value 4  | Value 5  | Value 6  |

## Sample Formula

$$E = mc^2$$

This is a mock result and not real OCR output.
"""

    async def table_to_markdown(self, image_bytes: bytes, meta: dict) -> str:
        """Mock table to markdown conversion."""
        return "| A | B |\n|---|---|\n| 1 | 2 |"

    async def formula_to_latex(self, image_bytes: bytes, meta: dict) -> str:
        """Mock formula to LaTeX conversion."""
        return "E = mc^2"


async def example_custom_implementation(pdf_path: Path) -> None:
    """
    Use a custom backend implementation.

    Args:
        pdf_path: Path to PDF file
    """
    print(f"\n{'='*60}")
    print("Example 5: Custom Backend Implementation")
    print(f"{'='*60}")

    # Initialize config
    config = init_config()

    # Create mock backend config
    mock_config = OcrBackendConfig(
        name="mock-backend",
        model="mock-model",
        base_url="http://localhost:9999",
        api_key=None,
        temperature=0.0,
        max_tokens=8192,
    )

    print(f"\nCreating custom MockBackend...")

    # Create custom backend instance
    backend = MockBackend(mock_config)

    # Create pipeline
    pipeline = HybridPipeline(config, backend=backend)

    # Convert
    print(f"\n🚀 Converting {pdf_path.name} with MockBackend...")
    result = await pipeline.convert_pdf(pdf_path)

    print(f"\n✅ Success!")
    print(f"   Pages: {result.processed_pages}")
    print(f"   Backend: {result.backend_name}")
    print(f"\n📝 Mock output preview:")
    print("-" * 60)
    print(result.markdown[:500])
    print("-" * 60)


# =============================================================================
# Main
# =============================================================================

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Custom backend configuration examples",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "pdf_file",
        type=Path,
        help="PDF file to convert"
    )

    parser.add_argument(
        "-b", "--backend",
        type=str,
        help="Backend name from config (e.g., 'nemotron-openrouter', 'deepseek-vllm')"
    )

    parser.add_argument(
        "-e", "--custom-endpoint",
        type=str,
        help="Custom endpoint URL (e.g., 'http://localhost:8000')"
    )

    parser.add_argument(
        "-m", "--model",
        type=str,
        help="Custom model name for OpenRouter"
    )

    parser.add_argument(
        "--vllm",
        type=str,
        help="vLLM server endpoint (e.g., 'http://localhost:8000')"
    )

    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock backend (for testing)"
    )

    parser.add_argument(
        "--all-examples",
        action="store_true",
        help="Run all examples (requires mock only)"
    )

    args = parser.parse_args()

    # Check if PDF exists
    if not args.pdf_file.exists():
        print(f"❌ Error: File not found: {args.pdf_file}")
        sys.exit(1)

    try:
        # Run examples based on arguments
        if args.all_examples:
            # Run all examples with mock backend
            asyncio.run(example_custom_implementation(args.pdf_file))

        elif args.mock:
            asyncio.run(example_custom_implementation(args.pdf_file))

        elif args.custom_endpoint:
            asyncio.run(example_custom_config(args.pdf_file, args.custom_endpoint))

        elif args.vllm:
            asyncio.run(example_local_vllm(args.pdf_file, args.vllm))

        elif args.model:
            asyncio.run(example_openrouter_custom_model(args.pdf_file, args.model))

        elif args.backend:
            asyncio.run(example_preconfigured_backend(args.pdf_file, args.backend))

        else:
            # Default: use config's default backend
            config = init_config()
            backend_name = config.backends.default
            asyncio.run(example_preconfigured_backend(args.pdf_file, backend_name))

    except DoclingHybridError as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n⚠️  Interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
