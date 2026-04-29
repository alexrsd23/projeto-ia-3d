import { useState, useEffect } from 'react';
import ReactFlow, { 
  Controls, Background, MiniMap, MarkerType,
  useNodesState, useEdgesState, Panel, Handle, Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import FamilyNode from './CharacterCards/FamilyNode';

// NÓ VIRTUAL DE CASAMENTO (Centro Gravitacional do Casal)
function UnionNode({ data }: { data: any }) {
  return (
    <div style={{ width: '16px', height: '16px', background: data.color || '#ec4899', borderRadius: '50%', border: '3px solid white', boxShadow: '0 1px 3px rgba(0,0,0,0.2)', zIndex: 10 }}>
      <Handle type="target" position={Position.Top} id="top" style={{ opacity: 0 }} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Left} id="left" style={{ opacity: 0 }} />
      <Handle type="target" position={Position.Right} id="right" style={{ opacity: 0 }} />
    </div>
  );
}

const nodeTypes = {
  familyNode: FamilyNode,
  unionNode: UnionNode,
};

export default function FamilyTreeViewport() {
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [loading, setLoading] = useState(true);

  const fetchTree = async () => {
    try {
      setLoading(true);
      const res = await fetch('http://127.0.0.1:8000/api/family/tree');
      const data = await res.json();

      const rfNodes: any[] = [];
      const rfEdges: any[] = [];
      
      const couples: any[] = [];
      const singles: any[] = [];
      const nodeToBlock: Record<string, string> = {};
      const processed = new Set<string>();

      // =======================================================
      // 1. ANÁLISE SOCIOLÓGICA (Agrupar Casais vs Solteiros)
      // =======================================================
      // Agrupa primeiro casamentos ativos
      data.edges.filter((e: any) => e.rel_type === 'MARRIED_TO').forEach((e: any) => {
        if (!processed.has(e.source) && !processed.has(e.target)) {
          const id = `FAM_${e.source}_${e.target}`;
          couples.push({ id, a: e.source, b: e.target, edge: e });
          nodeToBlock[e.source] = id;
          nodeToBlock[e.target] = id;
          processed.add(e.source);
          processed.add(e.target);
        }
      });

      // Agrupa em seguida viúvos que ainda não foram processados (monogamia sequencial)
      data.edges.filter((e: any) => e.rel_type === 'WIDOWED_FROM').forEach((e: any) => {
        if (!processed.has(e.source) && !processed.has(e.target)) {
          const id = `FAM_${e.source}_${e.target}`;
          couples.push({ id, a: e.source, b: e.target, edge: e });
          nodeToBlock[e.source] = id;
          nodeToBlock[e.target] = id;
          processed.add(e.source);
          processed.add(e.target);
        }
      });

      // Quem sobrou é solteiro
      data.nodes.forEach((n: any) => {
        if (!processed.has(n.id)) {
          singles.push(n);
          nodeToBlock[n.id] = n.id;
        }
      });

      // =======================================================
      // 2. MOTOR DAGRE (Mapeamento de Blocos Familiares)
      // =======================================================
      const g = new dagre.graphlib.Graph();
      g.setGraph({ rankdir: 'TB', ranksep: 500, nodesep: 300 });
      g.setDefaultEdgeLabel(() => ({}));

      // Injeta Blocos Largos (Casais) e Estreitos (Solteiros)
      couples.forEach(c => g.setNode(c.id, { width: 420, height: 260 })); // 180 + 60 gap + 180 = 420px
      singles.forEach(s => g.setNode(s.id, { width: 180, height: 260 }));

      // As relações de descendência conectam os Blocos
      data.edges.forEach((e: any) => {
        if (e.rel_type === 'PARENT_OF') {
          const srcBlock = nodeToBlock[e.source];
          const tgtBlock = nodeToBlock[e.target];
          if (srcBlock && tgtBlock) {
            g.setEdge(srcBlock, tgtBlock, { minlen: 1 });
          }
        }
      });

      dagre.layout(g);

      // =======================================================
      // 3. RENDERIZAÇÃO REACT FLOW (Desempacotar os Blocos)
      // =======================================================
      couples.forEach(c => {
        const pos = g.node(c.id);
        const nodeA = data.nodes.find((n: any) => n.id === c.a);
        const nodeB = data.nodes.find((n: any) => n.id === c.b);
        
        // Esposa/Marido Esquerdo
        rfNodes.push({
          id: nodeA.id, type: 'familyNode',
          data: { ...nodeA, health: nodeA.is_dead ? 0 : 100, inventoryJSON: "{}" },
          position: { x: pos.x - 210, y: pos.y - 130 }
        });
        
        // Esposa/Marido Direito
        rfNodes.push({
          id: nodeB.id, type: 'familyNode',
          data: { ...nodeB, health: nodeB.is_dead ? 0 : 100, inventoryJSON: "{}" },
          position: { x: pos.x + 30, y: pos.y - 130 }
        });

        const isWidowed = c.edge.rel_type === 'WIDOWED_FROM';
        const color = isWidowed ? '#64748b' : '#ec4899';
        const unionId = `union-${c.id}`;

        // Nó de União perfeitamente centrado
        rfNodes.push({
          id: unionId, type: 'unionNode',
          data: { color },
          position: { x: pos.x - 8, y: pos.y + 60 } // Ajustado visualmente abaixo do meio
        });

        // Ligar Marido e Esposa ao Centro (Linhas laterais em Esquadria)
        rfEdges.push({
          id: `e-m1-${c.id}`, source: c.a, target: unionId,
          sourceHandle: 'right-source', targetHandle: 'left',
          type: 'step', animated: !isWidowed,
          style: { stroke: color, strokeWidth: 2, strokeDasharray: isWidowed ? '5,5' : 'none' }
        });
        rfEdges.push({
          id: `e-m2-${c.id}`, source: c.b, target: unionId,
          sourceHandle: 'left-source', targetHandle: 'right',
          type: 'step', animated: !isWidowed,
          style: { stroke: color, strokeWidth: 2, strokeDasharray: isWidowed ? '5,5' : 'none' }
        });
      });

      singles.forEach(s => {
        const pos = g.node(s.id);
        rfNodes.push({
          id: s.id, type: 'familyNode',
          data: { ...s, health: s.is_dead ? 0 : 100, inventoryJSON: "{}" },
          position: { x: pos.x - 90, y: pos.y - 130 }
        });
      });

      // Filhos descem a partir da base do Nó de União para o Topo do Filho
      data.edges.forEach((e: any) => {
        if (e.rel_type === 'PARENT_OF') {
          const parentBlockId = nodeToBlock[e.source];
          const isCouple = couples.find(c => c.id === parentBlockId);
          const sourceId = isCouple ? `union-${isCouple.id}` : e.source;
          
          rfEdges.push({
            id: `e-p-${e.source}-${e.target}`,
            source: sourceId, target: e.target,
            sourceHandle: 'bottom', targetHandle: 'top',
            type: 'step', animated: true,
            markerEnd: { type: MarkerType.ArrowClosed, color: '#3b82f6' },
            style: { stroke: '#3b82f6', strokeWidth: 2 }
          });
        }
      });

      // Trata monogamia sequencial (Viuvez secundária de quem já foi agrupado em outro casamento)
      data.edges.forEach((e: any) => {
        if (e.rel_type === 'WIDOWED_FROM' || e.rel_type === 'MARRIED_TO') {
          const block1 = nodeToBlock[e.source];
          const block2 = nodeToBlock[e.target];
          if (block1 !== block2) {
            rfEdges.push({
              id: `e-cross-${e.source}-${e.target}`,
              source: e.source, target: e.target,
              sourceHandle: 'right-source', targetHandle: 'left-target',
              type: 'step',
              style: { stroke: '#64748b', strokeWidth: 2, strokeDasharray: '5,5' }
            });
          }
        }
      });

      // Remove duplicações residuais
      const uniqueEdges = rfEdges.filter((v, i, a) => a.findIndex(t => (t.id === v.id)) === i);
      
      setNodes(rfNodes);
      setEdges(uniqueEdges);
      setLoading(false);

    } catch (error) {
      console.error("Erro ao buscar árvore:", error);
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTree();
    const intervalId = setInterval(fetchTree, 10000); 
    return () => clearInterval(intervalId);
  }, []);

  if (loading && nodes.length === 0) return <div style={{ padding: '20px', color: '#64748b' }}>A estruturar sequenciamento genético...</div>;

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <ReactFlow
        nodes={nodes} edges={edges}
        onNodesChange={onNodesChange} onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        fitView minZoom={0.1}
      >
        <Background color="#cbd5e1" gap={16} />
        <Controls />
        <MiniMap nodeColor={(node) => node.type === 'unionNode' ? '#94a3b8' : (node.data.sex === 'F' ? '#f472b6' : '#60a5fa')} />
      </ReactFlow>
    </div>
  );
}