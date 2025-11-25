"""Performance and throughput benchmarks.

This module tests:
- Pages per minute (sequential processing)
- Pages per minute (concurrent processing)
- End-to-end conversion time
- Throughput with varying worker counts

Run with:
    pytest tests/benchmarks/test_performance.py -v --benchmark
"""

import asyncio
import time
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from docling_hybrid.orchestrator import HybridPipeline
from docling_hybrid.orchestrator.models import ConversionOptions


@pytest.mark.benchmark
class TestThroughputBenchmarks:
    """Benchmark tests for throughput measurements."""

    @pytest.mark.asyncio
    async def test_single_page_conversion_time(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_1_page: Path,
        fast_mock_backend,
    ):
        """Measure time to convert a single page."""
        # Patch backend to use fast mock
        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result = await benchmark_pipeline.convert_pdf(sample_pdf_1_page)
            elapsed = time.time() - start

            assert result.processed_pages == 1
            assert elapsed < 1.0, f"Single page took {elapsed:.2f}s (expected <1s)"

            print(f"\n  Single page conversion: {elapsed:.3f}s")

    @pytest.mark.asyncio
    async def test_pages_per_minute_10_pages(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
    ):
        """Measure pages/minute for 10-page document."""
        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result = await benchmark_pipeline.convert_pdf(sample_pdf_10_pages)
            elapsed = time.time() - start

            assert result.processed_pages == 10
            pages_per_minute = (result.processed_pages / elapsed) * 60

            # Should process at least 30 pages/minute with fast mock
            assert (
                pages_per_minute > 30
            ), f"Too slow: {pages_per_minute:.1f} pages/min (expected >30)"

            print(f"\n  10 pages in {elapsed:.2f}s")
            print(f"  Throughput: {pages_per_minute:.1f} pages/min")

    @pytest.mark.asyncio
    async def test_pages_per_minute_50_pages(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_50_pages: Path,
        fast_mock_backend,
    ):
        """Measure pages/minute for larger 50-page document."""
        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result = await benchmark_pipeline.convert_pdf(sample_pdf_50_pages)
            elapsed = time.time() - start

            assert result.processed_pages == 50
            pages_per_minute = (result.processed_pages / elapsed) * 60

            # Should maintain reasonable throughput even with more pages
            assert (
                pages_per_minute > 20
            ), f"Too slow: {pages_per_minute:.1f} pages/min (expected >20)"

            print(f"\n  50 pages in {elapsed:.2f}s")
            print(f"  Throughput: {pages_per_minute:.1f} pages/min")

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_realistic_api_latency_10_pages(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_10_pages: Path,
        slow_mock_backend,
    ):
        """Test with realistic VLM API latency (500ms per page)."""
        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=slow_mock_backend
        ):
            start = time.time()
            result = await benchmark_pipeline.convert_pdf(sample_pdf_10_pages)
            elapsed = time.time() - start

            assert result.processed_pages == 10
            pages_per_minute = (result.processed_pages / elapsed) * 60

            # With 500ms latency and parallel processing, should still be reasonable
            print(f"\n  10 pages with realistic latency: {elapsed:.2f}s")
            print(f"  Throughput: {pages_per_minute:.1f} pages/min")
            print(f"  Average time per page: {elapsed/10:.2f}s")


@pytest.mark.benchmark
class TestConcurrencyBenchmarks:
    """Benchmark tests for concurrent processing."""

    @pytest.mark.asyncio
    async def test_concurrent_vs_sequential_speedup(
        self,
        benchmark_config,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
    ):
        """Compare concurrent vs sequential processing."""
        # Test sequential (max_workers=1)
        benchmark_config.resources.max_workers = 1
        pipeline_sequential = HybridPipeline(benchmark_config)

        with patch.object(
            pipeline_sequential, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result_seq = await pipeline_sequential.convert_pdf(sample_pdf_10_pages)
            time_sequential = time.time() - start

        # Test concurrent (max_workers=4)
        benchmark_config.resources.max_workers = 4
        pipeline_concurrent = HybridPipeline(benchmark_config)

        with patch.object(
            pipeline_concurrent, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result_conc = await pipeline_concurrent.convert_pdf(sample_pdf_10_pages)
            time_concurrent = time.time() - start

        speedup = time_sequential / time_concurrent

        print(f"\n  Sequential (1 worker): {time_sequential:.2f}s")
        print(f"  Concurrent (4 workers): {time_concurrent:.2f}s")
        print(f"  Speedup: {speedup:.2f}x")

        # Should see at least 1.5x speedup with 4 workers
        assert (
            speedup > 1.5
        ), f"Insufficient speedup: {speedup:.2f}x (expected >1.5x)"

    @pytest.mark.asyncio
    async def test_scaling_with_worker_count(
        self,
        benchmark_config,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
    ):
        """Test throughput scaling with different worker counts."""
        worker_counts = [1, 2, 4, 8]
        results = {}

        for workers in worker_counts:
            benchmark_config.resources.max_workers = workers
            pipeline = HybridPipeline(benchmark_config)

            with patch.object(pipeline, "_get_backend", return_value=fast_mock_backend):
                start = time.time()
                result = await pipeline.convert_pdf(sample_pdf_10_pages)
                elapsed = time.time() - start

                pages_per_minute = (result.processed_pages / elapsed) * 60
                results[workers] = {
                    "time": elapsed,
                    "pages_per_min": pages_per_minute,
                }

        print("\n  Worker Scaling Results:")
        print("  Workers | Time (s) | Pages/min")
        print("  --------|----------|----------")
        for workers, data in results.items():
            print(
                f"  {workers:7} | {data['time']:8.2f} | {data['pages_per_min']:9.1f}"
            )

        # Should see improvement from 1 to 4 workers
        assert (
            results[4]["pages_per_min"] > results[1]["pages_per_min"]
        ), "4 workers should be faster than 1 worker"


@pytest.mark.benchmark
class TestRenderingBenchmarks:
    """Benchmark tests for PDF rendering performance."""

    @pytest.mark.asyncio
    async def test_page_rendering_time(self, sample_pdf_10_pages: Path):
        """Measure time to render pages to PNG."""
        from docling_hybrid.renderer import render_page_to_png_bytes

        times = []
        for page_idx in range(10):
            start = time.time()
            image_bytes = render_page_to_png_bytes(
                sample_pdf_10_pages, page_idx, dpi=150
            )
            elapsed = time.time() - start
            times.append(elapsed)

            assert len(image_bytes) > 0, "Image bytes should not be empty"

        avg_time = sum(times) / len(times)
        print(f"\n  Average rendering time: {avg_time:.3f}s per page")
        print(f"  Total for 10 pages: {sum(times):.3f}s")

        # Rendering should be fast (<0.5s per page at 150 DPI)
        assert avg_time < 0.5, f"Rendering too slow: {avg_time:.3f}s per page"

    @pytest.mark.asyncio
    async def test_dpi_impact_on_rendering(self, sample_pdf_1_page: Path):
        """Test how DPI affects rendering time and size."""
        from docling_hybrid.renderer import render_page_to_png_bytes

        dpi_values = [72, 150, 200, 300]
        results = {}

        for dpi in dpi_values:
            start = time.time()
            image_bytes = render_page_to_png_bytes(sample_pdf_1_page, 0, dpi=dpi)
            elapsed = time.time() - start

            results[dpi] = {
                "time": elapsed,
                "size_kb": len(image_bytes) / 1024,
            }

        print("\n  DPI Impact on Rendering:")
        print("  DPI | Time (s) | Size (KB)")
        print("  ----|----------|----------")
        for dpi, data in results.items():
            print(f"  {dpi:3} | {data['time']:8.3f} | {data['size_kb']:9.1f}")


@pytest.mark.benchmark
class TestEndToEndBenchmarks:
    """End-to-end conversion benchmarks."""

    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_complete_conversion_pipeline(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_10_pages: Path,
        fast_mock_backend,
        tmp_path: Path,
        resource_monitor,
    ):
        """Benchmark complete conversion including file I/O."""
        output_path = tmp_path / "output.md"

        resource_monitor.start()

        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result = await benchmark_pipeline.convert_pdf(
                sample_pdf_10_pages, output_path=output_path
            )
            elapsed = time.time() - start

        stats = resource_monitor.stop()

        assert result.processed_pages == 10
        assert output_path.exists()
        assert len(result.markdown) > 0

        pages_per_minute = (result.processed_pages / elapsed) * 60

        print(f"\n  Complete Pipeline (10 pages):")
        print(f"    Total time: {elapsed:.2f}s")
        print(f"    Throughput: {pages_per_minute:.1f} pages/min")
        print(f"    Peak memory: {stats['peak_memory_mb']:.1f} MB")
        print(f"    Output size: {len(result.markdown)} chars")

    @pytest.mark.asyncio
    async def test_max_pages_option(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_50_pages: Path,
        fast_mock_backend,
    ):
        """Test conversion with max_pages limit."""
        options = ConversionOptions(max_pages=10)

        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result = await benchmark_pipeline.convert_pdf(
                sample_pdf_50_pages, options=options
            )
            elapsed = time.time() - start

        assert result.processed_pages == 10
        assert result.total_pages == 50

        print(f"\n  Processed 10 of 50 pages in {elapsed:.2f}s")

    @pytest.mark.asyncio
    async def test_page_range_selection(
        self,
        benchmark_pipeline: HybridPipeline,
        sample_pdf_50_pages: Path,
        fast_mock_backend,
    ):
        """Test conversion with start_page and max_pages."""
        options = ConversionOptions(start_page=20, max_pages=5)

        with patch.object(
            benchmark_pipeline, "_get_backend", return_value=fast_mock_backend
        ):
            start = time.time()
            result = await benchmark_pipeline.convert_pdf(
                sample_pdf_50_pages, options=options
            )
            elapsed = time.time() - start

        assert result.processed_pages == 5
        assert result.total_pages == 50

        print(f"\n  Processed pages 20-24 in {elapsed:.2f}s")


@pytest.mark.benchmark
class TestLatencyBenchmarks:
    """API latency and response time benchmarks."""

    @pytest.mark.asyncio
    async def test_backend_call_latency(self, fast_mock_backend):
        """Measure backend API call latency."""
        latencies = []

        for i in range(10):
            start = time.time()
            await fast_mock_backend.page_to_markdown(
                b"dummy_image_bytes", page_num=i + 1, doc_id="test-doc"
            )
            elapsed = time.time() - start
            latencies.append(elapsed)

        avg_latency = sum(latencies) / len(latencies)
        min_latency = min(latencies)
        max_latency = max(latencies)
        p95_latency = sorted(latencies)[int(len(latencies) * 0.95)]

        print(f"\n  Backend API Latency (10 calls):")
        print(f"    Average: {avg_latency*1000:.1f}ms")
        print(f"    Min: {min_latency*1000:.1f}ms")
        print(f"    Max: {max_latency*1000:.1f}ms")
        print(f"    P95: {p95_latency*1000:.1f}ms")

    @pytest.mark.asyncio
    async def test_concurrent_backend_calls(self, fast_mock_backend):
        """Test latency under concurrent load."""
        num_concurrent = 10

        async def make_call(i):
            start = time.time()
            await fast_mock_backend.page_to_markdown(
                b"dummy_image_bytes", page_num=i, doc_id="test-doc"
            )
            return time.time() - start

        start_total = time.time()
        latencies = await asyncio.gather(*[make_call(i) for i in range(num_concurrent)])
        total_time = time.time() - start_total

        avg_latency = sum(latencies) / len(latencies)

        print(f"\n  {num_concurrent} Concurrent Backend Calls:")
        print(f"    Total time: {total_time:.2f}s")
        print(f"    Avg latency: {avg_latency*1000:.1f}ms")
        print(f"    Effective throughput: {num_concurrent/total_time:.1f} calls/sec")
