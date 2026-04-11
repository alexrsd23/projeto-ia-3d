import { useState, useEffect, useCallback } from 'react';
import ReactFlow, { 
  Controls, 
  Background, 
  MiniMap, 
  MarkerType,
  useNodesState, 
  useEdgesState,
  Panel
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import FamilyNode from './CharacterCards/FamilyNode';

// Registamos o nosso Nó Customizado (A Polaroid)
const nodeTypes = {
  familyNode: FamilyNode,
};

export default function FamilyTreeViewport() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  // A Magia do Dagre: Calcula as posições X e Y automaticamente
  const getLayoutedElements = (rawNodes: any[], rawEdges: any[]) => {
    const dagreGraph = new dagre.graphlib.Graph();
    dagreGraph.setDefaultEdgeLabel(() => ({}));
    
    // rankdir 'TB' = Top to Bottom (Cima para Baixo)
    dagreGraph.setGraph({ rankdir: 'TB', ranksep: 120, nodesep: 80 });

    rawNodes.forEach((node) => {
      // O tamanho aproximado da nossa Polaroid
      dagreGraph.setNode(node.id, { width: 180, height: 260 });
    });

    rawEdges.forEach((edge) => {
      dagreGraph.setEdge(edge.source, edge.target);
    });

    dagre.layout(dagreGraph);

    const layoutedNodes = rawNodes.map((node) => {
      const nodeWithPosition = dagreGraph.node(node.id);
      return {
        ...node,
        targetPosition: 'top',
        sourcePosition: 'bottom',
        // O Dagre ancora no centro, o React Flow ancora na ponta esquerda. Compensamos isso:
        position: {
          x: nodeWithPosition.x - 180 / 2,
          y: nodeWithPosition.y - 260 / 2,
        },
      };
    });

    return { layoutedNodes, layoutedEdges: rawEdges };
  };

  const fetchTree = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://127.0.0.1:8000/api/family/tree');
      const data = await res.json();

      // 1. Mapeia os Nós (Pessoas)
      const formattedNodes = data.nodes.map((n: any) => ({
        id: n.id,
        type: 'familyNode',
        data: {
          // Adaptamos os dados para enganar a Polaroid e ela achar que está a ler o BD normal
          id: n.id, type: n.type, name: n.name, profession: n.profession, 
          color: n.color, married: n.married, health: n.is_dead ? 0 : 100,
          inventoryJSON: "{}" // Enviamos vazio para não dar erro nos Plobs
        },
        position: { x: 0, y: 0 } // O Dagre vai reescrever isto
      }));

      // 2. Mapeia as Arestas (Relações)
      const formattedEdges = data.edges.map((e: any, index: number) => {
        let edgeColor = '#94a3b8';
        let edgeStyle = { strokeWidth: 2, strokeDasharray: 'none' };
        let type = 'smoothstep';
        let marker = undefined;
        let animated = false;

        if (e.rel_type === 'MARRIED_TO') {
          edgeColor = '#ec4899'; // Rosa para Casamentos
          type = 'bezier';
          animated = true; // A linha de casamento vai mover-se suavemente
        } else if (e.rel_type === 'WIDOWED_FROM') {
          edgeColor = '#64748b'; // Cinza Escuro
          edgeStyle = { strokeWidth: 2, strokeDasharray: '5 5' }; // Pontilhado de Luto
          type = 'bezier';
        } else if (e.rel_type === 'PARENT_OF') {
          edgeColor = '#3b82f6'; // Azul Forte para Sangue
          marker = { type: MarkerType.ArrowClosed, color: edgeColor };
        }

        return {
          id: `e${index}-${e.source}-${e.target}`,
          source: e.source,
          target: e.target,
          type: type,
          animated: animated,
          style: { stroke: edgeColor, ...edgeStyle },
          markerEnd: marker,
        };
      });

      // 3. Aplica a Matemática de Layout
      const { layoutedNodes, layoutedEdges } = getLayoutedElements(formattedNodes, formattedEdges);
      
      setNodes(layoutedNodes);
      setEdges(layoutedEdges);
      setLoading(false);

    } catch (error) {
      console.error("Erro ao buscar árvore:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTree();
    // Podemos atualizar a cada 10 segundos, mas para árvores gigantes o ideal é atualizar por botão manual!
    const intervalId = setInterval(fetchTree, 10000); 
    return () => clearInterval(intervalId);
  }, []);

  if (loading && nodes.length === 0) return <div style={{ padding: '20px' }}>A carregar Genética...</div>;

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView // Dá zoom automático para mostrar a árvore toda ao abrir
        minZoom={0.1}
      >
        <Background color="#cbd5e1" gap={16} />
        <Controls />
        <MiniMap nodeColor={(node) => {
          // O Mini Mapa pinta pontinhos cor-de-rosa para mulheres e azuis para homens
          return node.data.sex === 'F' ? '#f472b6' : '#60a5fa';
        }} />
        
        {/* Legenda Flutuante */}
        <Panel position="top-right" style={{ backgroundColor: 'rgba(255,255,255,0.9)', padding: '10px', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
          <div style={{ fontSize: '12px', fontWeight: 'bold', marginBottom: '5px' }}>Legenda:</div>
          <div style={{ fontSize: '11px', color: '#3b82f6' }}>— Descendência (Pai/Mãe)</div>
          <div style={{ fontSize: '11px', color: '#ec4899' }}>〰️ Casamento Ativo</div>
          <div style={{ fontSize: '11px', color: '#64748b' }}>- - Luto Histórico</div>
        </Panel>
      </ReactFlow>
    </div>
  );
}