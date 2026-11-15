"""CLI benchmark runner for QORA Phase 2 evaluation."""

import json
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.resolve()))

from services.api.ai.benchmark_dataset import BenchmarkDatasetGenerator
from services.api.ai.evaluator import BenchmarkEvaluator


def main() -> None:
    print("=" * 60)
    print("QORA Phase 2: Quantum AI Benchmark Evaluation Suite")
    print("=" * 60)

    print("\n1. Generating fault-injected benchmark dataset...")
    dataset = BenchmarkDatasetGenerator.generate()
    dataset_path = BenchmarkDatasetGenerator.save_to_file(dataset)
    print(f"   ✓ Created {len(dataset.records)} benchmark records across 6 fault types.")
    print(f"   ✓ Saved dataset to: {dataset_path}")

    print("\n2. Running benchmark evaluation on held-out test split...")
    report = BenchmarkEvaluator.evaluate(dataset, split="held_out")
    report_path = BenchmarkEvaluator.save_report_to_file(report)
    print(f"   ✓ Evaluation complete. Saved report to: {report_path}")

    print("\n" + "=" * 60)
    print("SUMMARY RESULTS")
    print("=" * 60)
    print(f"• Diagnosis Classification Accuracy: {report.diagnosis.classification_accuracy * 100:.1f}%")
    print(f"• Diagnosis Macro F1-Score:          {report.diagnosis.f1_score * 100:.1f}%")
    print(f"• Repair Semantic Correctness Rate:  {report.repair.semantic_correctness_rate * 100:.1f}%")
    print(f"• Repair Average State Fidelity:     {report.repair.avg_fidelity * 100:.1f}%")
    print(f"• Generation Equivalence Rate:       {report.generation.equivalence_rate * 100:.1f}%")
    print(f"• Optimization Equivalence Rate:     {report.optimization.equivalence_verification_rate * 100:.1f}%")
    print(f"• Average Gate Reduction:            {report.optimization.avg_gate_reduction_percent:.1f}%")
    print(f"• Overall Grounded Composite Score:  {report.overall_score * 100:.1f}%")
    print("=" * 60)


if __name__ == "__main__":
    main()
