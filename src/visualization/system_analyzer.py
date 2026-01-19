"""코드베이스를 분석하여 CrewAI 시스템 구조를 추출하는 모듈"""

import ast
from pathlib import Path
from typing import Dict, List, Set
import networkx as nx


class SystemAnalyzer:
    """코드베이스를 분석하여 CrewAI 시스템 구조를 추출"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.crews: Dict[str, Dict] = {}
        self.tasks: List[Dict] = []
        self.tools: Set[str] = set()
        self.graph = nx.DiGraph()
    
    def analyze_crews(self):
        """src/crews 디렉토리에서 Crew 클래스 분석"""
        crews_dir = self.project_root / "src" / "crews"
        
        if not crews_dir.exists():
            return
        
        for crew_file in crews_dir.glob("*.py"):
            if crew_file.name == "__init__.py":
                continue
            
            # 파일명을 기반으로 Crew 이름 추정
            # 예: price_crew.py -> PriceCrew
            crew_name = crew_file.stem.replace("_crew", "").title() + "Crew"
            
            with open(crew_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # import 문에서 도구 찾기
            imports = self._extract_imports(content)
            tools = [imp.split('.')[-1] for imp in imports if 'tool' in imp.lower()]
            
            self.crews[crew_name] = {
                'file': str(crew_file),
                'tools': tools,
                'methods': self._extract_methods(content)
            }
            
            # 그래프에 추가
            self.graph.add_node(crew_name, node_type="crew")
            for tool in tools:
                if tool:
                    self.tools.add(tool)
                    self.graph.add_node(tool, node_type="tool")
                    self.graph.add_edge(crew_name, tool, edge_type="uses")
    
    def analyze_orchestrator(self):
        """OrchestratorFlow 분석"""
        flow_file = self.project_root / "src" / "orchestrator" / "flow.py"
        
        if not flow_file.exists():
            return
        
        self.graph.add_node("OrchestratorFlow", node_type="orchestrator")
    
    def analyze_planner(self):
        """Planner에서 기본 작업 분석"""
        planner_file = self.project_root / "src" / "orchestrator" / "planner.py"
        
        if not planner_file.exists():
            return
        
        # 예시 작업들 (실제로는 AST를 사용하여 더 정확하게 파싱 가능)
        base_tasks = [
            {"name": "price_analysis", "crew": "PriceCrew"},
            {"name": "news_analysis", "crew": "NewsCrew"},
            {"name": "fundamental_analysis", "crew": "FundamentalsCrew"}
        ]
        
        for task in base_tasks:
            self.tasks.append(task)
            self.graph.add_node(task["name"], node_type="task")
            self.graph.add_edge("OrchestratorFlow", task["name"], edge_type="creates")
            if task["crew"] in self.crews or task["crew"] in [n for n in self.graph.nodes()]:
                self.graph.add_edge(task["name"], task["crew"], edge_type="assigned_to")
    
    def analyze_triggers(self):
        """TriggerEngine에서 동적 작업 분석"""
        triggers_file = self.project_root / "src" / "orchestrator" / "triggers.py"
        
        if not triggers_file.exists():
            return
        
        # 트리거 기반 작업들
        trigger_tasks = [
            {"name": "options_liquidity_analysis", "crew": "OptionsLiquidityCrew", "trigger": "Volatility Spike"},
            {"name": "legal_analysis", "crew": "RegulationLegalCrew", "trigger": "Legal Red Flags"},
            {"name": "supplementary_research", "crew": "NewsCrew", "trigger": "Insufficient Evidence"}
        ]
        
        for task in trigger_tasks:
            self.tasks.append(task)
            trigger_name = task["trigger"]
            self.graph.add_node(trigger_name, node_type="trigger")
            self.graph.add_node(task["name"], node_type="task")
            self.graph.add_edge(trigger_name, task["name"], edge_type="triggers")
            if task["crew"] in self.crews or task["crew"] in [n for n in self.graph.nodes()]:
                self.graph.add_edge(task["name"], task["crew"], edge_type="assigned_to")
    
    def _extract_imports(self, content: str) -> List[str]:
        """코드에서 import 문 추출"""
        imports = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
        except SyntaxError:
            pass
        return imports
    
    def _extract_methods(self, content: str) -> List[str]:
        """클래스의 메서드 이름 추출"""
        methods = []
        try:
            tree = ast.parse(content)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    methods.append(node.name)
        except SyntaxError:
            pass
        return methods
    
    def build_complete_graph(self):
        """전체 그래프 구축"""
        self.analyze_crews()
        self.analyze_orchestrator()
        self.analyze_planner()
        self.analyze_triggers()
        
        return self.graph
