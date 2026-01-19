"""NetworkX를 사용한 그래프 시각화"""

from pathlib import Path

try:
    import matplotlib.pyplot as plt
    import networkx as nx
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False

try:
    import plotly.graph_objects as go
    import plotly.offline as pyo
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

from src.visualization.system_analyzer import SystemAnalyzer


class NetworkXVisualizer:
    """NetworkX를 사용한 그래프 시각화"""
    
    def __init__(self, analyzer: SystemAnalyzer):
        if not MATPLOTLIB_AVAILABLE:
            raise ImportError(
                "Matplotlib이 설치되지 않았습니다. 'pip install matplotlib'를 실행하세요."
            )
        self.analyzer = analyzer
        self.graph = analyzer.build_complete_graph()
    
    def visualize_static(self, output_path: str = "crew_graph.png"):
        """정적 그래프 이미지 생성"""
        plt.figure(figsize=(16, 10))
        
        # 레이아웃 설정
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # 노드 타입별 색상 지정
        node_colors = []
        for node in self.graph.nodes():
            node_type = self.graph.nodes[node].get('node_type', 'default')
            color_map = {
                'orchestrator': '#FF6B6B',
                'crew': '#4ECDC4',
                'task': '#95E1D3',
                'tool': '#F38181',
                'trigger': '#AA96DA'
            }
            node_colors.append(color_map.get(node_type, '#CCCCCC'))
        
        # 노드 그리기
        nx.draw_networkx_nodes(
            self.graph, pos,
            node_color=node_colors,
            node_size=3000,
            alpha=0.9
        )
        
        # 엣지 그리기
        nx.draw_networkx_edges(
            self.graph, pos,
            edge_color='gray',
            arrows=True,
            arrowsize=20,
            alpha=0.6,
            connectionstyle="arc3,rad=0.1"
        )
        
        # 레이블 그리기
        labels = {node: node for node in self.graph.nodes()}
        nx.draw_networkx_labels(
            self.graph, pos,
            labels,
            font_size=8,
            font_weight='bold'
        )
        
        plt.title("CrewAI Agent System Graph", fontsize=16, fontweight='bold')
        plt.axis('off')
        plt.tight_layout()
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"그래프가 {output_path}에 저장되었습니다.")
    
    def visualize_interactive(self, output_path: str = "crew_graph.html"):
        """인터랙티브 그래프 생성 (Plotly 사용)"""
        if not PLOTLY_AVAILABLE:
            print("Plotly가 설치되지 않았습니다. 'pip install plotly'를 실행하세요.")
            return
        
        # 레이아웃 계산
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # 엣지 추적
        edge_x = []
        edge_y = []
        for edge in self.graph.edges():
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]
            edge_x.extend([x0, x1, None])
            edge_y.extend([y0, y1, None])
        
        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=2, color='#888'),
            hoverinfo='none',
            mode='lines'
        )
        
        # 노드 추적
        node_x = []
        node_y = []
        node_text = []
        node_colors = []
        
        color_map = {
            'orchestrator': '#FF6B6B',
            'crew': '#4ECDC4',
            'task': '#95E1D3',
            'tool': '#F38181',
            'trigger': '#AA96DA'
        }
        
        for node in self.graph.nodes():
            x, y = pos[node]
            node_x.append(x)
            node_y.append(y)
            node_text.append(node)
            node_type = self.graph.nodes[node].get('node_type', 'default')
            node_colors.append(color_map.get(node_type, '#CCCCCC'))
        
        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode='markers+text',
            hoverinfo='text',
            text=node_text,
            textposition="middle center",
            marker=dict(
                size=30,
                color=node_colors,
                line=dict(width=2, color='white')
            )
        )
        
        fig = go.Figure(
            data=[edge_trace, node_trace],
            layout=go.Layout(
                title=dict(text="CrewAI Agent System Graph (Interactive)", font=dict(size=16)),
                showlegend=False,
                hovermode='closest',
                margin=dict(b=20, l=5, r=5, t=40),
                annotations=[
                    dict(
                        text="노드를 클릭하여 상세 정보 확인",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor='left', yanchor='bottom',
                        font=dict(color="#888", size=12)
                    )
                ],
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
        )
        
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        pyo.plot(fig, filename=output_path, auto_open=False)
        print(f"인터랙티브 그래프가 {output_path}에 저장되었습니다.")
