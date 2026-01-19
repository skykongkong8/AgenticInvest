"""Mermaid 다이어그램 코드 생성"""

from pathlib import Path
from src.visualization.system_analyzer import SystemAnalyzer


class MermaidGenerator:
    """Mermaid 다이어그램 코드 생성"""
    
    def __init__(self, analyzer: SystemAnalyzer):
        self.analyzer = analyzer
        self.graph = analyzer.build_complete_graph()
    
    def generate_mermaid(self) -> str:
        """Mermaid 다이어그램 코드 생성"""
        lines = ["graph TD"]
        
        # 노드 정의
        node_map = {}  # 원본 이름 -> 안전한 ID 매핑
        
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('node_type', 'default')
            node_id = node.replace(" ", "_").replace("-", "_").replace(".", "_")
            node_map[node] = node_id
            
            style_map = {
                'orchestrator': f'{node_id}["{node}"]:::orchestrator',
                'crew': f'{node_id}["{node}"]:::crew',
                'task': f'{node_id}["{node}"]:::task',
                'tool': f'{node_id}["{node}"]:::tool',
                'trigger': f'{node_id}["{node}"]:::trigger'
            }
            
            if node_type in style_map:
                lines.append(f"    {style_map[node_type]}")
        
        # 엣지 정의
        for edge in self.graph.edges():
            source_id = node_map.get(edge[0], edge[0].replace(" ", "_").replace("-", "_"))
            target_id = node_map.get(edge[1], edge[1].replace(" ", "_").replace("-", "_"))
            edge_type = self.graph.edges[edge].get('edge_type', '')
            label = f"|{edge_type}|" if edge_type else ""
            lines.append(f"    {source_id} -->{label} {target_id}")
        
        # 스타일 정의
        lines.extend([
            "",
            "    classDef orchestrator fill:#FF6B6B,stroke:#333,stroke-width:3px",
            "    classDef crew fill:#4ECDC4,stroke:#333,stroke-width:2px",
            "    classDef task fill:#95E1D3,stroke:#333,stroke-width:2px",
            "    classDef tool fill:#F38181,stroke:#333,stroke-width:2px",
            "    classDef trigger fill:#AA96DA,stroke:#333,stroke-width:2px"
        ])
        
        return "\n".join(lines)
    
    def save_mermaid(self, output_path: str = "crew_graph.mmd"):
        """Mermaid 파일 저장"""
        mermaid_code = self.generate_mermaid()
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(mermaid_code)
        
        print(f"Mermaid 다이어그램이 {output_path}에 저장되었습니다.")
        return mermaid_code
