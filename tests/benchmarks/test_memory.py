"""Memory profiling and usage benchmarks.

This module tests:
- Peak memory usage
- Memory growth patterns
- Memory leaks
- Resource cleanup

Run with:
    pytest tests/benchmarks/test_memory.py -v --benchmark
"""

import asyncio
import gc
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from docling_hybrid.orchestrator import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionOptions


@pytest.mark.benchmark
class TestMemoryUsage:
    """Memory usage benchmarks."""

    @pytest.mark.asyncio
    async def test_peak_memory_10_pages(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Measure peak memory for 10-page PDF."""
        resource_monitor.start()

        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            result = await benchmark_pipeline.convert_pdf(sample_pdf_10_pages)

        stats = resource_monitor.stop()

        assert result.processed_pages == 10

        print(f"\n  Memory Usage (10 pages):")
        print(f"    Peak: {stats['peak_memory_mb']:.1f} MB")
        print(f"    Delta: {stats['delta_memory_mb']:.1f} MB")
        print(f"    Time: {stats['elapsed_seconds']:.2f}s")

        # Peak memory should be reasonable for 10 pages (<200MB)
        assert (
            stats["peak_memory_mb"] < 200
        ), f"Memory too high: {stats['peak_memory_mb']:.1f}MB"

    @pytest.mark.asyncio
    async def test_peak_memory_50_pages(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_50_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Measure peak memory for 50-page PDF."""
        resource_monitor.start()

        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            result = await benchmark_pipeline.convert_pdf(sample_pdf_50_pages)

        stats = resource_monitor.stop()

        assert result.processed_pages == 50

        print(f"\n  Memory Usage (50 pages):")
        print(f"    Peak: {stats['peak_memory_mb']:.1f} MB")
        print(f"    Delta: {stats['delta_memory_mb']:.1f} MB")
        print(f"    Per page: {stats['delta_memory_mb']/50:.2f} MB")
        print(f"    Time: {stats['elapsed_seconds']:.2f}s")

        # Peak memory should scale reasonably with pages (<500MB for 50 pages)
        assert (
            stats["peak_memory_mb"] < 500
        ), f"Memory too high: {stats['peak_memory_mb']:.1f}MB"

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_peak_memory_100_pages(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_100_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Measure peak memory for 100-page PDF (stress test)."""
        resource_monitor.start()

        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            result = await benchmark_pipeline.convert_pdf(sample_pdf_100_pages)

        stats = resource_monitor.stop()

        assert result.processed_pages == 100

        print(f"\n  Memory Usage (100 pages):")
        print(f"    Peak: {stats['peak_memory_mb']:.1f} MB")
        print(f"    Delta: {stats['delta_memory_mb']:.1f} MB")
        print(f"    Per page: {stats['delta_memory_mb']/100:.2f} MB")
        print(f"    Time: {stats['elapsed_seconds']:.2f}s")

        # Peak memory should be acceptable even for 100 pages (<1GB)
        assert (
            stats["peak_memory_mb"] < 1024
        ), f"Memory too high: {stats['peak_memory_mb']:.1f}MB"


@pytest.mark.benchmark
class TestMemoryScaling:
    """Test how memory scales with document size."""

    @pytest.mark.asyncio
    async def test_memory_scaling_by_page_count(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_1_page: Path,
        sample_pdf_10_pages: Path,
        sample_pdf_50_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Test memory scaling with different page counts."""
        test_cases = [
            (sample_pdf_1_page, 1),
            (sample_pdf_10_pages, 10),
            (sample_pdf_50_pages, 50),
        ]

        results = {}

        for pdf_path, expected_pages in test_cases:
            gc.collect()  # Clean up before each test
            await asyncio.sleep(0.1)

            resource_monitor.start()

            with patch.object(
                benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
            ):
                result = await benchmark_pipeline.convert_pdf(pdf_path)

            stats = resource_monitor.stop()

            assert result.processed_pages == expected_pages

            results[expected_pages] = {
                "peak_mb": stats["peak_memory_mb"],
                "delta_mb": stats["delta_memory_mb"],
                "per_page_mb": stats["delta_memory_mb"] / expected_pages,
            }

        print("\n  Memory Scaling by Page Count:")
        print("  Pages | Peak (MB) | Delta (MB) | Per Page (MB)")
        print("  ------|-----------|------------|---------------")
        for pages, data in sorted(results.items()):
            print(
                f"  {pages:5} | {data['peak_mb']:9.1f} | "
                f"{data['delta_mb']:10.1f} | {data['per_page_mb']:13.2f}"
            )

        # Memory should scale roughly linearly (allow some overhead)
        # Check that 50-page per-page usage is not more than 3x 1-page
        if results[1]["per_page_mb"] > 0:
            ratio = results[50]["per_page_mb"] / results[1]["per_page_mb"]
            assert ratio < 3.0, f"Memory scaling too poor: {ratio:.2f}x increase"

    @pytest.mark.asyncio
    async def test_memory_with_different_dpi(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Test how DPI affects memory usage."""
        dpi_values = [72, 150, 300]
        results = {}

        for dpi in dpi_values:
            gc.collect()
            await asyncio.sleep(0.1)

            options = ConversionOptions(dpi=dpi)
            resource_monitor.start()

            with patch.object(
                benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
            ):
                result = await benchmark_pipeline.convert_pdf(
                    sample_pdf_10_pages, options=options
                )

            stats = resource_monitor.stop()

            results[dpi] = {
                "peak_mb": stats["peak_memory_mb"],
                "delta_mb": stats["delta_memory_mb"],
            }

        print("\n  Memory Usage by DPI (10 pages):")
        print("  DPI | Peak (MB) | Delta (MB)")
        print("  ----|-----------|------------")
        for dpi, data in sorted(results.items()):
            print(f"  {dpi:3} | {data['peak_mb']:9.1f} | {data['delta_mb']:10.1f}")


@pytest.mark.benchmark
class TestMemoryLeaks:
    """Test for potential memory leaks."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_repeated_conversions_no_leak(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
    ):
        """Test that repeated conversions don't leak memory."""
        import tracemalloc

        tracemalloc.start()

        memory_samples = []
        num_iterations = 5

        for i in range(num_iterations):
            gc.collect()  # Force garbage collection

            before = tracemalloc.get_traced_memory()[0]

            with patch.object(
                benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
            ):
                result = await benchmark_pipeline.convert_pdf(sample_pdf_10_pages)

            gc.collect()  # Force cleanup

            after = tracemalloc.get_traced_memory()[0]
            delta_mb = (after - before) / (1024 * 1024)

            memory_samples.append(delta_mb)

            assert result.processed_pages == 10

        tracemalloc.stop()

        print(f"\n  Memory Delta Across {num_iterations} Iterations:")
        for i, delta in enumerate(memory_samples, 1):
            print(f"    Iteration {i}: {delta:+.1f} MB")

        # Memory growth should stabilize (last iteration shouldn't be much higher than first)
        if len(memory_samples) >= 2:
            first_delta = memory_samples[0]
            last_delta = memory_samples[-1]

            # Allow up to 2x growth (due to caches, etc.)
            if first_delta > 0:
                growth_ratio = last_delta / first_delta
                assert (
                    growth_ratio < 2.0
                ), f"Possible memory leak: {growth_ratio:.2f}x growth"

    @pytest.mark.asyncio
    async def test_backend_cleanup(
        self, benchmark_config, sample_pdf_10_pages: Path, fast_mock_backend
    ):
        """Test that backend resources are properly cleaned up."""
        import tracemalloc

        tracemalloc.start()

        initial_memory = tracemalloc.get_traced_memory()[0]

        # Create and use pipeline
        pipeline = HybridPipeline(benchmark_config)

        with patch.object(pipeline, "_get_backend", return_value=fast_mock_backend):
            result = await pipeline.convert_pdf(sample_pdf_10_pages)

        # Clean up
        if pipeline._backend:
            await pipeline._backend.close()

        gc.collect()

        final_memory = tracemalloc.get_traced_memory()[0]
        delta_mb = (final_memory - initial_memory) / (1024 * 1024)

        tracemalloc.stop()

        print(f"\n  Memory after cleanup: {delta_mb:+.1f} MB")

        # After cleanup, memory should not grow significantly
        assert delta_mb < 50, f"Memory not cleaned up: {delta_mb:.1f} MB remaining"


@pytest.mark.benchmark
class TestResourceConstraints:
    """Test behavior under resource constraints."""

    @pytest.mark.asyncio
    async def test_low_memory_mode(
        self,
        benchmark_config,
        sample_pdf_50_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Test conversion with low memory constraints."""
        # Configure for low memory usage
        benchmark_config.resources.max_workers = 1  # Sequential processing
        benchmark_config.resources.max_memory_mb = 512  # Low memory limit

        pipeline = HybridPipeline(benchmark_config)

        resource_monitor.start()

        with patch.object(pipeline, "_get_backend", return_value=fast_mock_backend):
            result = await pipeline.convert_pdf(sample_pdf_50_pages)

        stats = resource_monitor.stop()

        assert result.processed_pages == 50

        print(f"\n  Low Memory Mode (50 pages, 1 worker):")
        print(f"    Peak: {stats['peak_memory_mb']:.1f} MB")
        print(f"    Time: {stats['elapsed_seconds']:.2f}s")

        # Should respect memory constraint (with some overhead)
        assert (
            stats["peak_memory_mb"] < 1024
        ), f"Exceeded memory budget: {stats['peak_memory_mb']:.1f}MB"

    @pytest.mark.asyncio
    async def test_memory_with_max_pages_limit(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_100_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Test that max_pages helps control memory usage."""
        options = ConversionOptions(max_pages=10)

        resource_monitor.start()

        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            result = await benchmark_pipeline.convert_pdf(
                sample_pdf_100_pages, options=options
            )

        stats = resource_monitor.stop()

        assert result.processed_pages == 10
        assert result.total_pages == 100

        print(f"\n  Memory with max_pages=10 (from 100-page PDF):")
        print(f"    Peak: {stats['peak_memory_mb']:.1f} MB")
        print(f"    Time: {stats['elapsed_seconds']:.2f}s")

        # Should use memory comparable to a 10-page doc, not 100-page
        assert (
            stats["peak_memory_mb"] < 300
        ), f"Memory too high for 10 pages: {stats['peak_memory_mb']:.1f}MB"


@pytest.mark.benchmark
class TestConcurrentMemory:
    """Test memory usage under concurrent load."""

    @pytest.mark.asyncio
    async def test_memory_with_concurrent_workers(
        self,
        benchmark_config,
        sample_pdf_50_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Test memory usage with different worker counts."""
        worker_counts = [1, 2, 4]
        results = {}

        for workers in worker_counts:
            gc.collect()
            await asyncio.sleep(0.1)

            benchmark_config.resources.max_workers = workers
            pipeline = HybridPipeline(benchmark_config)

            resource_monitor.start()

            with patch.object(pipeline, "_get_backend", return_value=fast_mock_backend):
                result = await pipeline.convert_pdf(sample_pdf_50_pages)

            stats = resource_monitor.stop()

            results[workers] = {
                "peak_mb": stats["peak_memory_mb"],
                "delta_mb": stats["delta_memory_mb"],
                "time_s": stats["elapsed_seconds"],
            }

        print("\n  Memory vs Worker Count (50 pages):")
        print("  Workers | Peak (MB) | Delta (MB) | Time (s)")
        print("  --------|-----------|------------|----------")
        for workers, data in sorted(results.items()):
            print(
                f"  {workers:7} | {data['peak_mb']:9.1f} | "
                f"{data['delta_mb']:10.1f} | {data['time_s']:8.2f}"
            )

        # More workers should use more memory but not excessively
        # 4 workers shouldn't use more than 2x memory of 1 worker
        if results[1]["delta_mb"] > 0:
            ratio = results[4]["delta_mb"] / results[1]["delta_mb"]
            assert ratio < 2.5, f"Memory scaling too poor: {ratio:.2f}x with 4 workers"

    @pytest.mark.asyncio
    async def test_memory_multiple_concurrent_documents(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
        resource_monitor,
    ):
        """Test memory when processing multiple documents concurrently."""
        num_docs = 3

        async def convert_doc(doc_num):
            with patch.object(
                benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
            ):
                return await benchmark_pipeline.convert_pdf(sample_pdf_10_pages)

        resource_monitor.start()

        results = await asyncio.gather(*[convert_doc(i) for i in range(num_docs)])

        stats = resource_monitor.stop()

        assert all(r.processed_pages == 10 for r in results)

        print(f"\n  Memory with {num_docs} Concurrent Documents:")
        print(f"    Peak: {stats['peak_memory_mb']:.1f} MB")
        print(f"    Delta: {stats['delta_memory_mb']:.1f} MB")
        print(f"    Per doc: {stats['delta_memory_mb']/num_docs:.1f} MB")
        print(f"    Time: {stats['elapsed_seconds']:.2f}s")
