"""Graphviz를 사용한 그래프 시각화"""

try:
    from graphviz import Digraph
    GRAPHVIZ_AVAILABLE = True
except ImportError:
    GRAPHVIZ_AVAILABLE = False

from src.visualization.system_analyzer import SystemAnalyzer


class GraphvizVisualizer:
    """Graphviz를 사용한 그래프 시각화"""
    
    def __init__(self, analyzer: SystemAnalyzer):
        if not GRAPHVIZ_AVAILABLE:
            raise ImportError(
                "Graphviz가 설치되지 않았습니다. "
                "'pip install graphviz'를 실행하고 "
                "시스템에 Graphviz를 설치하세요 (https://graphviz.org/download/)"
            )
        self.analyzer = analyzer
        self.graph = analyzer.build_complete_graph()
    
    def generate_dot_file(self, output_path: str = "crew_graph.dot"):
        """DOT 파일 생성"""
        dot = Digraph(comment='CrewAI Agent System', format='png')
        dot.attr(rankdir='TB', size='12,8')
        dot.attr('node', style='rounded,filled')
        
        # 노드 타입별 스타일
        node_styles = {
            'orchestrator': {'fillcolor': '#FF6B6B', 'shape': 'diamond'},
            'crew': {'fillcolor': '#4ECDC4', 'shape': 'ellipse'},
            'task': {'fillcolor': '#95E1D3', 'shape': 'box'},
            'tool': {'fillcolor': '#F38181', 'shape': 'hexagon'},
            'trigger': {'fillcolor': '#AA96DA', 'shape': 'octagon'}
        }
        
        # 노드 추가
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('node_type', 'default')
            style = node_styles.get(node_type, {'fillcolor': '#CCCCCC', 'shape': 'box'})
            dot.node(node, node, **style)
        
        # 엣지 추가
        for edge in self.graph.edges():
            edge_type = self.graph.edges[edge].get('edge_type', '')
            label = edge_type if edge_type else ''
            dot.edge(edge[0], edge[1], label=label)
        
        # 파일 저장
        output_name = output_path.replace('.dot', '')
        dot.render(output_name, cleanup=True)
        print(f"DOT 파일이 생성되었습니다: {output_path}")
        print(f"PNG 이미지가 생성되었습니다: {output_name}.png")
        
        return dot
