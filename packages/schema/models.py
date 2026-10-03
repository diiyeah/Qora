"""Circuit contract shared with the frontend and future Python consumers."""

from typing import Annotated, Literal, Self

from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, model_validator
from pydantic_core import PydanticCustomError

GateName = Literal[
    "h", "x", "y", "z", "s", "sdg", "t", "tdg",
    "rx", "ry", "rz", "p", "cx", "cz", "swap", "ccx",
]
Index = Annotated[int, Field(ge=0, strict=True)]
GATE_ARITY: dict[GateName, int] = {
    "h": 1, "x": 1, "y": 1, "z": 1, "s": 1, "sdg": 1,
    "t": 1, "tdg": 1, "rx": 1, "ry": 1, "rz": 1, "p": 1,
    "cx": 2, "cz": 2, "swap": 2, "ccx": 3,
}
PARAMETER_GATES: frozenset[GateName] = frozenset({"rx", "ry", "rz", "p"})


class ContractModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Gate(ContractModel):
    name: GateName
    qubits: list[Index]
    params: list[FiniteFloat]
    layer: Index

    @model_validator(mode="after")
    def validate_arguments(self) -> Self:
        arity = GATE_ARITY[self.name]
        if len(self.qubits) != arity or len(set(self.qubits)) != arity:
            raise PydanticCustomError(
                "invalid_gate", "{gate} requires {arity} distinct qubits",
                {"gate": self.name, "arity": arity},
            )
        parameter_count = 1 if self.name in PARAMETER_GATES else 0
        if len(self.params) != parameter_count:
            raise PydanticCustomError(
                "invalid_gate", "{gate} requires {count} parameters",
                {"gate": self.name, "count": parameter_count},
            )
        return self


class Measurement(ContractModel):
    qubit: Index
    clbit: Index


class CircuitMetadata(ContractModel):
    framework: str = "qiskit"
    task_id: str | None = None


class Circuit(ContractModel):
    """Qubit 0 is the first wire; measurements occur after all gates.

    ``layer`` records the caller's zero-based drawing position. It is not a
    substitute for circuit depth, which will be calculated by the analyzer.
    """

    num_qubits: Annotated[int, Field(ge=1, strict=True)]
    num_clbits: Index
    gates: list[Gate]
    measurements: list[Measurement]
    metadata: CircuitMetadata

    @model_validator(mode="after")
    def validate_indices(self) -> Self:
        for gate in self.gates:
            for qubit in gate.qubits:
                if qubit >= self.num_qubits:
                    raise PydanticCustomError(
                        "qubit_out_of_range", "Qubit {qubit} is outside this circuit",
                        {"qubit": qubit, "num_qubits": self.num_qubits},
                    )
        for measurement in self.measurements:
            if measurement.qubit >= self.num_qubits:
                raise PydanticCustomError(
                    "qubit_out_of_range", "Measured qubit {qubit} is outside this circuit",
                    {"qubit": measurement.qubit, "num_qubits": self.num_qubits},
                )
            if measurement.clbit >= self.num_clbits:
                raise PydanticCustomError(
                    "measurement", "Classical bit {clbit} is outside this circuit",
                    {"clbit": measurement.clbit, "num_clbits": self.num_clbits},
                )
        return self

