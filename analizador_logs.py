from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import re
from typing import Iterable, Optional


RECOGNIZED_LEVELS = ("INFO", "WARNING", "ERROR")
SEVERITY_TOKEN_RE = re.compile(r"^\s*\[([^\]]+)\]")
VALID_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
# Un token con estructura de fecha, pero que no cumple YYYY-MM-DD, se
# considera fecha inválida y no fecha ausente.
DATE_LIKE_RE = re.compile(
    r"^(?:\d{4}[-/]\d{1,2}[-/]\d{1,2}|\d{8})$"
)


@dataclass
class LineAnalysis:
    """Resultado del análisis de una línea no vacía."""

    severity: Optional[str]
    severity_status: str
    date_status: str
    message: str
    complete: bool
    problems: list[str] = field(default_factory=list)


@dataclass
class LogStatistics:
    """Contadores acumulados del archivo analizado."""

    total_events: int = 0
    info: int = 0
    warning: int = 0
    error: int = 0
    unknown_severity: int = 0
    missing_severity: int = 0
    valid_dates: int = 0
    invalid_dates: int = 0
    missing_dates: int = 0
    incomplete_or_malformed: int = 0
    valid_records: int = 0


def _extract_severity_and_content(line: str) -> tuple[Optional[str], str, str]:
    """Extrae el token inicial de severidad y el contenido restante.

    Si no existe un token entre corchetes al inicio, la severidad se marca
    como ausente y la línea completa queda disponible para detectar la fecha.
    """

    match = SEVERITY_TOKEN_RE.match(line)
    if match is None:
        return None, line.strip(), "missing"

    severity = match.group(1)
    content = line[match.end() :].strip()
    if severity in RECOGNIZED_LEVELS:
        return severity, content, "recognized"
    return severity, content, "unknown"


def _validate_date_and_message(content: str) -> tuple[str, str, list[str]]:
    """Clasifica la fecha y devuelve también el mensaje restante.

    Criterio del campo de fecha:
    el primer token después de la severidad es el campo candidato. Si coincide
    con una forma de fecha (YYYY-MM-DD, variantes con / o ocho dígitos), se
    clasifica como fecha inválida cuando no cumple exactamente YYYY-MM-DD o
    cuando datetime demuestra que la fecha no existe. Si no parece una fecha,
    se clasifica como ausente y el contenido completo se conserva como mensaje.
    """

    if not content:
        return "missing", "", ["missing_date", "missing_message"]

    parts = content.split(maxsplit=1)
    first_token = parts[0]
    message = parts[1].strip() if len(parts) == 2 else ""

    if VALID_DATE_RE.fullmatch(first_token):
        try:
            datetime.strptime(first_token, "%Y-%m-%d")
        except ValueError:
            problems = ["invalid_date"]
            if not message:
                problems.append("missing_message")
            return "invalid", message, problems

        problems = [] if message else ["missing_message"]
        return "valid", message, problems

    if DATE_LIKE_RE.fullmatch(first_token):
        problems = ["invalid_date"]
        if not message:
            problems.append("missing_message")
        return "invalid", message, problems

    # El primer token no parece una fecha. Se conserva como parte del mensaje.
    return "missing", content, ["missing_date"]


def analyze_line(line: str) -> Optional[LineAnalysis]:
    """Analiza una línea y devuelve None para líneas vacías."""

    if not line.strip():
        return None

    severity, content, severity_status = _extract_severity_and_content(line)
    date_status, message, problems = _validate_date_and_message(content)

    if severity_status == "unknown":
        problems.append("unknown_severity")
    elif severity_status == "missing":
        problems.append("missing_severity")

    complete = (
        severity_status == "recognized"
        and date_status == "valid"
        and bool(message)
    )

    return LineAnalysis(
        severity=severity,
        severity_status=severity_status,
        date_status=date_status,
        message=message,
        complete=complete,
        problems=problems,
    )


def update_statistics(statistics: LogStatistics, result: LineAnalysis) -> None:
    """Actualiza las estadísticas con un único resultado de línea."""

    statistics.total_events += 1

    if result.severity == "INFO":
        statistics.info += 1
    elif result.severity == "WARNING":
        statistics.warning += 1
    elif result.severity == "ERROR":
        statistics.error += 1
    elif result.severity_status == "unknown":
        statistics.unknown_severity += 1
    else:
        statistics.missing_severity += 1

    if result.date_status == "valid":
        statistics.valid_dates += 1
    elif result.date_status == "invalid":
        statistics.invalid_dates += 1
    else:
        statistics.missing_dates += 1

    if result.complete:
        statistics.valid_records += 1
    else:
        # Una línea con varios problemas solo incrementa una vez este contador.
        statistics.incomplete_or_malformed += 1


def analyze_lines(lines: Iterable[str]) -> LogStatistics:
    """Analiza un conjunto de líneas y devuelve sus estadísticas."""

    statistics = LogStatistics()
    for line in lines:
        result = analyze_line(line)
        if result is not None:
            update_statistics(statistics, result)
    return statistics


def analyze_file(path: str | Path) -> LogStatistics:
    """Lee y analiza un archivo UTF-8."""

    file_path = Path(path)
    with file_path.open("r", encoding="utf-8") as file:
        return analyze_lines(file)


def format_statistics(statistics: LogStatistics) -> str:
    """Genera el resumen de resultados para la consola."""

    return "\n".join(
        [
            "\nResumen del análisis",
            "--------------------",
            f"Total de eventos: {statistics.total_events}",
            f"INFO: {statistics.info}",
            f"WARNING: {statistics.warning}",
            f"ERROR: {statistics.error}",
            f"Severidades desconocidas: {statistics.unknown_severity}",
            f"Severidades ausentes: {statistics.missing_severity}",
            f"Fechas válidas: {statistics.valid_dates}",
            f"Fechas inválidas: {statistics.invalid_dates}",
            f"Fechas ausentes: {statistics.missing_dates}",
            f"Líneas incompletas o mal formadas: {statistics.incomplete_or_malformed}",
            f"Registros completamente válidos: {statistics.valid_records}",
        ]
    )


def request_file_path() -> Optional[Path]:
    """Solicita rutas hasta que el usuario cancele o entregue una existente."""

    while True:
        raw_path = input(
            "Escribe la ruta del archivo UTF-8: "
        ).strip()

        if raw_path.lower() == "cancelar":
            return None

        path = Path(raw_path)
        if path.is_file():
            return path

        print("Advertencia: el archivo no existe o no es un archivo regular.")


def main() -> None:
    """Punto de entrada de la aplicación de consola."""

    while True:
        path = request_file_path()
        if path is None:
            print("Operación cancelada.")
            return

        try:
            statistics = analyze_file(path)
        except (OSError, UnicodeError) as error:
            print(f"Advertencia: no se pudo leer el archivo: {error}")
            print("Introduce otra ruta o escribe 'cancelar'.")
            continue

        print(format_statistics(statistics))
        return


if __name__ == "__main__":
    main()
