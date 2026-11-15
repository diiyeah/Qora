"""Quantum Tool Registry for AI reasoning and function calling."""

import json
from collections.abc import Callable
from typing import Any

from packages.schema.models import Circuit
from services.api.ai.diagnostics import QuantumDiagnosticsEngine
from services.api.ai.optimizer import CircuitOptimizerEngine
from services.api.ai.repair_engine import QuantumCircuitRepairEngine
from services.api.ai.verification import CircuitVerificationEngine
from services.api.errors import PlatformError
from services.api.tools.circuit_ops import (
    analyze_circuit,
    calculate_metrics,
    compare_circuits,
    get_measurement_distribution,
    get_statevector,
    simulate_circuit,
)


class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: dict[str, Any],
    ) -> None:
        self.name = name
        self.description = description
        self.handler = handler
        self.parameters = parameters

    def to_schema(self) -> dict[str, Any]:
        """Format as JSON schema compatible with LLM function declarations."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._register_default_tools()

    def register(
        self,
        name: str,
        description: str,
        handler: Callable[..., Any],
        parameters: dict[str, Any],
    ) -> None:
        self._tools[name] = ToolDefinition(name, description, handler, parameters)

    def get_definitions(self) -> list[dict[str, Any]]:
        return [tool.to_schema() for tool in self._tools.values()]

    def execute(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        """Execute a tool by name with arguments and return a serializable dict."""
        if name not in self._tools:
            return {"error": f"Tool '{name}' is not registered."}

        tool = self._tools[name]
        try:
            # If circuit dict is passed in arguments, convert to canonical Circuit
            parsed_args = dict(args)
            if "circuit" in parsed_args and isinstance(parsed_args["circuit"], dict):
                parsed_args["circuit"] = Circuit.model_validate(parsed_args["circuit"])
            if "circuit_a" in parsed_args and isinstance(parsed_args["circuit_a"], dict):
                parsed_args["circuit_a"] = Circuit.model_validate(parsed_args["circuit_a"])
            if "circuit_b" in parsed_args and isinstance(parsed_args["circuit_b"], dict):
                parsed_args["circuit_b"] = Circuit.model_validate(parsed_args["circuit_b"])

            raw_res = tool.handler(**parsed_args)
            if hasattr(raw_res, "model_dump"):
                dumped: dict[str, Any] = raw_res.model_dump(mode="json")
                return dumped
            if isinstance(raw_res, dict):
                return {str(k): v for k, v in raw_res.items()}
            if isinstance(raw_res, (list, str, int, float, bool)) or raw_res is None:
                return {"result": raw_res}
            return {"result": str(raw_res)}
        except PlatformError as exc:
            return {"error": exc.error.message, "type": exc.error.type}
        except Exception as exc:
            return {"error": str(exc)}

    def _register_default_tools(self) -> None:
        circuit_param_schema = {
            "type": "object",
            "properties": {
                "circuit": {
                    "type": "object",
                    "description": "Canonical QORA circuit object",
                },
            },
            "required": ["circuit"],
        }

        self.register(
            name="analyze_circuit",
            description="Analyze quantum circuit structure, total gates, depth, and CNOT count.",
            handler=analyze_circuit,
            parameters=circuit_param_schema,
        )

        self.register(
            name="simulate_circuit",
            description="Simulate circuit on Aer backend and retrieve measurement counts.",
            handler=simulate_circuit,
            parameters={
                "type": "object",
                "properties": {
                    "circuit": {"type": "object", "description": "Canonical QORA circuit"},
                    "shots": {"type": "integer", "default": 1024},
                    "seed": {"type": "integer", "nullable": True},
                },
                "required": ["circuit"],
            },
        )

        self.register(
            name="get_measurement_distribution",
            description="Compute normalized measurement probabilities from circuit simulation.",
            handler=get_measurement_distribution,
            parameters={
                "type": "object",
                "properties": {
                    "circuit": {"type": "object", "description": "Canonical QORA circuit"},
                    "shots": {"type": "integer", "default": 1024},
                    "seed": {"type": "integer", "nullable": True},
                },
                "required": ["circuit"],
            },
        )

        self.register(
            name="get_statevector",
            description="Compute quantum state amplitudes before measurement.",
            handler=get_statevector,
            parameters=circuit_param_schema,
        )

        self.register(
            name="calculate_metrics",
            description="Calculate key resource metrics: depth, gate count, CNOT count.",
            handler=calculate_metrics,
            parameters=circuit_param_schema,
        )

        self.register(
            name="compare_circuits",
            description="Compare two circuits for equivalence and metric differences.",
            handler=compare_circuits,
            parameters={
                "type": "object",
                "properties": {
                    "circuit_a": {"type": "object", "description": "First circuit"},
                    "circuit_b": {"type": "object", "description": "Second circuit"},
                },
                "required": ["circuit_a", "circuit_b"],
            },
        )

        self.register(
            name="diagnose_error",
            description="Diagnose quantum programming or circuit logic errors across 9 categories.",
            handler=QuantumDiagnosticsEngine.diagnose,
            parameters={
                "type": "object",
                "properties": {
                    "circuit": {"type": "object", "description": "Canonical QORA circuit", "nullable": True},
                    "source_code": {"type": "string", "nullable": True},
                    "expected_behavior": {"type": "string", "nullable": True},
                    "expected_distribution": {"type": "object", "nullable": True},
                    "shots": {"type": "integer", "default": 1024},
                    "seed": {"type": "integer", "nullable": True},
                },
            },
        )

        self.register(
            name="repair_circuit",
            description="Propose structured repairs, gate replacements, and code diffs for faulty circuits.",
            handler=QuantumCircuitRepairEngine.propose_repair,
            parameters={
                "type": "object",
                "properties": {
                    "circuit": {"type": "object", "description": "Canonical QORA circuit"},
                    "source_code": {"type": "string", "nullable": True},
                    "expected_behavior": {"type": "string", "nullable": True},
                    "expected_distribution": {"type": "object", "nullable": True},
                    "iteration": {"type": "integer", "default": 1},
                },
                "required": ["circuit"],
            },
        )

        self.register(
            name="optimize_circuit",
            description="Optimize quantum circuit to reduce depth, gate count, or CNOTs while preserving equivalence.",
            handler=CircuitOptimizerEngine.optimize,
            parameters={
                "type": "object",
                "properties": {
                    "circuit": {"type": "object", "description": "Canonical QORA circuit to optimize"},
                    "level": {"type": "integer", "default": 2},
                    "shots": {"type": "integer", "default": 1024},
                    "seed": {"type": "integer", "nullable": True},
                },
                "required": ["circuit"],
            },
        )

        self.register(
            name="verify_circuit",
            description="Verify circuit fidelity, TVD, and correctness against reference or expected behavior.",
            handler=CircuitVerificationEngine.verify,
            parameters={
                "type": "object",
                "properties": {
                    "circuit": {"type": "object", "description": "Canonical QORA circuit to verify"},
                    "reference_circuit": {"type": "object", "description": "Reference circuit", "nullable": True},
                    "expected_behavior": {"type": "string", "nullable": True},
                    "expected_distribution": {"type": "object", "nullable": True},
                    "shots": {"type": "integer", "default": 1024},
                    "seed": {"type": "integer", "nullable": True},
                },
                "required": ["circuit"],
            },
        )


default_tool_registry = ToolRegistry()
