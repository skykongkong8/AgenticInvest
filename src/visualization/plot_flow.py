"""CrewAI Flow 시각화를 위한 CLI 엔트리포인트 및 헬퍼."""

from __future__ import annotations

from pathlib import Path
from typing import Dict

from src.visualization.graphviz_visualizer import GraphvizVisualizer
from src.visualization.mermaid_generator import MermaidGenerator
from src.visualization.networkx_visualizer import NetworkXVisualizer
from src.visualization.system_analyzer import SystemAnalyzer


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def plot_flow_command(output_dir: Path | str = "outputs") -> None:
    """`crewai flow plot`에서 실행될 엔트리포인트."""
    run_visualization(Path(output_dir))


def run_visualization(output_dir: Path) -> Dict[str, Path]:
    """시스템 분석 후 다양한 시각화 아티팩트를 생성한다."""
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    analyzer = SystemAnalyzer(project_root=str(PROJECT_ROOT))

    results: Dict[str, Path] = {}

    try:
        nx_visualizer = NetworkXVisualizer(analyzer)
        nx_visualizer.visualize_static(str(output_dir / "crew_graph_static.png"))
        results["networkx_static"] = output_dir / "crew_graph_static.png"
        nx_visualizer.visualize_interactive(str(output_dir / "crew_graph_interactive.html"))
        results["networkx_interactive"] = output_dir / "crew_graph_interactive.html"
    except ImportError as exc:  # Matplotlib 또는 NetworkX 미설치
        print(f"[SKIP] NetworkX 시각화 실패: {exc}")
    except Exception as exc:  # 실행 중 오류
        print(f"[WARN] NetworkX 시각화 중 오류: {exc}")

    try:
        gv_visualizer = GraphvizVisualizer(analyzer)
        dot_path = output_dir / "crew_graph.dot"
        gv_visualizer.generate_dot_file(str(dot_path))
        results["graphviz_dot"] = dot_path
        # Graphviz가 생성한 PNG는 dot_path와 동일한 베이스 이름을 사용
        results["graphviz_png"] = output_dir / "crew_graph.png"
    except ImportError as exc:
        print(f"[SKIP] Graphviz 시각화 실패: {exc}")
    except Exception as exc:
        print(f"[WARN] Graphviz 시각화 중 오류: {exc}")

    mermaid_generator = MermaidGenerator(analyzer)
    mermaid_path = output_dir / "crew_graph.mmd"
    mermaid_generator.save_mermaid(str(mermaid_path))
    results["mermaid"] = mermaid_path

    _print_summary(output_dir)
    return results


def _print_summary(output_dir: Path) -> None:
    """생성된 아티팩트들을 정리해서 요약 출력."""
    output_dir = output_dir.resolve()
    files_to_check = [
        ("정적 이미지", output_dir / "crew_graph_static.png"),
        ("인터랙티브 그래프", output_dir / "crew_graph_interactive.html"),
        ("Graphviz DOT", output_dir / "crew_graph.dot"),
        ("Graphviz PNG", output_dir / "crew_graph.png"),
        ("Mermaid 다이어그램", output_dir / "crew_graph.mmd"),
    ]

    print("\n" + "=" * 60)
    print("생성된 시각화 파일:")
    print("=" * 60)

    for label, path in files_to_check:
        status = "[OK]" if path.exists() else "[SKIP]"
        print(f"  {status} {label}: {path}")


if __name__ == "__main__":
    plot_flow_command()
