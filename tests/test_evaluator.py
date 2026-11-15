from pathlib import Path

from packages.schema.ai import (
    BenchmarkEvaluationReport,
    DiagnosisEvaluationMetrics,
    GenerationEvaluationMetrics,
    OptimizationEvaluationMetrics,
    RepairEvaluationMetrics,
)
from services.api.ai.benchmark_dataset import BenchmarkDatasetGenerator
from services.api.ai.evaluator import BenchmarkEvaluator


def test_evaluator_generation() -> None:
    gen_metrics = BenchmarkEvaluator.evaluate_generation()
    assert isinstance(gen_metrics, GenerationEvaluationMetrics)
    assert gen_metrics.total_cases == 4
    assert gen_metrics.schema_validation_rate >= 0.75
    assert gen_metrics.execution_success_rate >= 0.75
    assert gen_metrics.equivalence_rate >= 0.75


def test_evaluator_optimization() -> None:
    opt_metrics = BenchmarkEvaluator.evaluate_optimization()
    assert isinstance(opt_metrics, OptimizationEvaluationMetrics)
    assert opt_metrics.total_cases == 4
    assert opt_metrics.avg_gate_reduction_percent > 0.0
    assert opt_metrics.equivalence_verification_rate == 1.0


def test_evaluator_full_report() -> None:
    dataset = BenchmarkDatasetGenerator.generate()
    report = BenchmarkEvaluator.evaluate(dataset, split="development")

    assert isinstance(report, BenchmarkEvaluationReport)
    assert report.diagnosis.total_cases > 0
    assert report.repair.total_cases > 0
    assert report.generation.total_cases > 0
    assert report.optimization.total_cases > 0
    assert 0.0 <= report.overall_score <= 1.0


def test_evaluator_save_report(tmp_path: Path) -> None:
    dataset = BenchmarkDatasetGenerator.generate()
    # Evaluate a subset for speed
    report = BenchmarkEvaluator.evaluate(dataset, split="development")
    file_path = str(tmp_path / "test_report.json")
    saved_path = BenchmarkEvaluator.save_report_to_file(report, file_path)

    assert Path(saved_path).exists()
