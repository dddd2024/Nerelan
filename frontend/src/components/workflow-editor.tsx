import { useState, useCallback, useRef, useEffect } from "react";
import { 
  Plus, 
  Trash2, 
  Play, 
  Save, 
  Undo, 
  Redo,
  ZoomIn,
  ZoomOut,
  Maximize,
  Settings
} from "lucide-react";
import { cn } from "@/lib/cn";
import { Button } from "@/components/ui/button";

interface WorkflowNode {
  id: string;
  type: "start" | "end" | "agent" | "condition" | "parallel" | "loop";
  label: string;
  x: number;
  y: number;
  config?: any;
}

interface WorkflowEdge {
  id: string;
  source: string;
  target: string;
  label?: string;
}

interface Workflow {
  id: string;
  name: string;
  description?: string;
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}

interface WorkflowEditorProps {
  workflow?: Workflow;
  onSave?: (workflow: Workflow) => void;
  onRun?: (workflow: Workflow) => void;
  readOnly?: boolean;
}

const defaultWorkflow: Workflow = {
  id: "workflow-1",
  name: "新工作流",
  description: "描述您的工作流",
  nodes: [
    { id: "start", type: "start", label: "开始", x: 100, y: 200 },
    { id: "end", type: "end", label: "结束", x: 700, y: 200 },
  ],
  edges: [],
};

export function WorkflowEditor({ 
  workflow = defaultWorkflow, 
  onSave, 
  onRun,
  readOnly = false 
}: WorkflowEditorProps) {
  const [currentWorkflow, setCurrentWorkflow] = useState<Workflow>(workflow);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const [zoom, setZoom] = useState(1);
  const [pan, setPan] = useState({ x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });
  const svgRef = useRef<SVGSVGElement>(null);

  const handleNodeMouseDown = useCallback((nodeId: string, e: React.MouseEvent) => {
    if (readOnly) return;
    
    e.stopPropagation();
    setSelectedNode(nodeId);
    setIsDragging(true);
    
    const node = currentWorkflow.nodes.find((n) => n.id === nodeId);
    if (node) {
      setDragOffset({
        x: e.clientX - node.x,
        y: e.clientY - node.y,
      });
    }
  }, [readOnly, currentWorkflow.nodes]);

  const handleMouseMove = useCallback((e: React.MouseEvent) => {
    if (isDragging && selectedNode) {
      const newX = e.clientX - dragOffset.x;
      const newY = e.clientY - dragOffset.y;
      
      setCurrentWorkflow((prev) => ({
        ...prev,
        nodes: prev.nodes.map((node) =>
          node.id === selectedNode
            ? { ...node, x: newX, y: newY }
            : node
        ),
      }));
    } else if (isPanning) {
      const dx = e.clientX - panStart.x;
      const dy = e.clientY - panStart.y;
      setPan((prev) => ({
        x: prev.x + dx,
        y: prev.y + dy,
      }));
      setPanStart({ x: e.clientX, y: e.clientY });
    }
  }, [isDragging, selectedNode, dragOffset, isPanning, panStart]);

  const handleMouseUp = useCallback(() => {
    setIsDragging(false);
    setIsPanning(false);
  }, []);

  const handleSvgMouseDown = useCallback((e: React.MouseEvent) => {
    if (e.target === svgRef.current) {
      setIsPanning(true);
      setPanStart({ x: e.clientX, y: e.clientY });
      setSelectedNode(null);
    }
  }, []);

  const handleAddNode = useCallback((type: WorkflowNode["type"]) => {
    const newNode: WorkflowNode = {
      id: `node-${Date.now()}`,
      type,
      label: type === "agent" ? "新Agent" : type === "condition" ? "条件" : type,
      x: 300 + Math.random() * 200,
      y: 200 + Math.random() * 100,
    };
    
    setCurrentWorkflow((prev) => ({
      ...prev,
      nodes: [...prev.nodes, newNode],
    }));
  }, []);

  const handleDeleteNode = useCallback((nodeId: string) => {
    if (nodeId === "start" || nodeId === "end") return;
    
    setCurrentWorkflow((prev) => ({
      ...prev,
      nodes: prev.nodes.filter((n) => n.id !== nodeId),
      edges: prev.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
    }));
    setSelectedNode(null);
  }, []);

  const handleConnect = useCallback((sourceId: string, targetId: string) => {
    const edgeExists = currentWorkflow.edges.some(
      (e) => e.source === sourceId && e.target === targetId
    );
    
    if (!edgeExists) {
      const newEdge: WorkflowEdge = {
        id: `edge-${Date.now()}`,
        source: sourceId,
        target: targetId,
      };
      
      setCurrentWorkflow((prev) => ({
        ...prev,
        edges: [...prev.edges, newEdge],
      }));
    }
  }, [currentWorkflow.edges]);

  const handleZoomIn = useCallback(() => {
    setZoom((prev) => Math.min(2, prev + 0.1));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom((prev) => Math.max(0.5, prev - 0.1));
  }, []);

  const handleResetView = useCallback(() => {
    setZoom(1);
    setPan({ x: 0, y: 0 });
  }, []);

  const renderNode = (node: WorkflowNode) => {
    const isSelected = selectedNode === node.id;
    const nodeWidth = 120;
    const nodeHeight = 60;
    
    return (
      <g key={node.id}>
        {/* Node rectangle */}
        <rect
          x={node.x - nodeWidth / 2}
          y={node.y - nodeHeight / 2}
          width={nodeWidth}
          height={nodeHeight}
          rx={8}
          className={cn(
            "cursor-pointer transition-all",
            isSelected ? "stroke-ra-accent stroke-2" : "stroke-ra-border",
            node.type === "start" && "fill-emerald-500/20",
            node.type === "end" && "fill-red-500/20",
            node.type === "agent" && "fill-blue-500/20",
            node.type === "condition" && "fill-amber-500/20",
            node.type === "parallel" && "fill-purple-500/20",
            node.type === "loop" && "fill-cyan-500/20",
          )}
          onMouseDown={(e) => handleNodeMouseDown(node.id, e)}
        />
        
        {/* Node label */}
        <text
          x={node.x}
          y={node.y + 4}
          textAnchor="middle"
          className="fill-ra-text text-xs pointer-events-none select-none"
        >
          {node.label}
        </text>
        
        {/* Delete button (only when selected and not read-only) */}
        {isSelected && !readOnly && node.type !== "start" && node.type !== "end" && (
          <g
            className="cursor-pointer"
            onClick={() => handleDeleteNode(node.id)}
          >
            <circle
              cx={node.x + nodeWidth / 2 - 10}
              cy={node.y - nodeHeight / 2 + 10}
              r={10}
              className="fill-red-500"
            />
            <text
              x={node.x + nodeWidth / 2 - 10}
              y={node.y - nodeHeight / 2 + 14}
              textAnchor="middle"
              className="fill-white text-xs"
            >
              ×
            </text>
          </g>
        )}
      </g>
    );
  };

  const renderEdge = (edge: WorkflowEdge) => {
    const sourceNode = currentWorkflow.nodes.find((n) => n.id === edge.source);
    const targetNode = currentWorkflow.nodes.find((n) => n.id === edge.target);
    
    if (!sourceNode || !targetNode) return null;
    
    const midX = (sourceNode.x + targetNode.x) / 2;
    const midY = (sourceNode.y + targetNode.y) / 2;
    
    return (
      <g key={edge.id}>
        <path
          d={`M ${sourceNode.x} ${sourceNode.y} Q ${midX} ${sourceNode.y} ${midX} ${midY} Q ${midX} ${targetNode.y} ${targetNode.x} ${targetNode.y}`}
          className="fill-none stroke-ra-border stroke-2"
          markerEnd="url(#arrowhead)"
        />
        {edge.label && (
          <text
            x={midX}
            y={midY - 10}
            textAnchor="middle"
            className="fill-ra-text-secondary text-xs"
          >
            {edge.label}
          </text>
        )}
      </g>
    );
  };

  return (
    <div className="flex flex-col h-full bg-ra-base rounded-xl border border-ra-border overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between px-4 py-2 border-b border-ra-border bg-ra-light">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-medium text-ra-text">工作流编辑器</h3>
          <span className="text-xs text-ra-text-tertiary">
            {currentWorkflow.nodes.length} 个节点
          </span>
        </div>
        
        <div className="flex items-center gap-2">
          {!readOnly && (
            <>
              <div className="flex items-center gap-1 border-r border-ra-border pr-2 mr-2">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAddNode("agent")}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  Agent
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAddNode("condition")}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  条件
                </Button>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => handleAddNode("parallel")}
                >
                  <Plus className="h-4 w-4 mr-1" />
                  并行
                </Button>
              </div>
              
              <Button
                variant="outline"
                size="sm"
                onClick={() => onSave?.(currentWorkflow)}
              >
                <Save className="h-4 w-4 mr-1" />
                保存
              </Button>
            </>
          )}
          
          <Button
            variant="default"
            size="sm"
            onClick={() => onRun?.(currentWorkflow)}
          >
            <Play className="h-4 w-4 mr-1" />
            运行
          </Button>
        </div>
      </div>

      {/* Canvas */}
      <div className="flex-1 relative overflow-hidden">
        <svg
          ref={svgRef}
          className="w-full h-full"
          onMouseDown={handleSvgMouseDown}
          onMouseMove={handleMouseMove}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
        >
          <defs>
            <marker
              id="arrowhead"
              markerWidth="10"
              markerHeight="7"
              refX="9"
              refY="3.5"
              orient="auto"
            >
              <polygon
                points="0 0, 10 3.5, 0 7"
                className="fill-ra-border"
              />
            </marker>
          </defs>
          
          <g
            transform={`translate(${pan.x}, ${pan.y}) scale(${zoom})`}
          >
            {/* Grid */}
            <pattern
              id="grid"
              width="20"
              height="20"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 20 0 L 0 0 0 20"
                fill="none"
                className="stroke-ra-border/30"
                strokeWidth="0.5"
              />
            </pattern>
            <rect width="100%" height="100%" fill="url(#grid)" />
            
            {/* Edges */}
            {currentWorkflow.edges.map(renderEdge)}
            
            {/* Nodes */}
            {currentWorkflow.nodes.map(renderNode)}
          </g>
        </svg>

        {/* Zoom controls */}
        <div className="absolute bottom-4 right-4 flex items-center gap-1 bg-ra-light border border-ra-border rounded-lg p-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            className="h-8 w-8 p-0"
          >
            <ZoomOut className="h-4 w-4" />
          </Button>
          <span className="text-xs text-ra-text-secondary px-2">
            {Math.round(zoom * 100)}%
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            className="h-8 w-8 p-0"
          >
            <ZoomIn className="h-4 w-4" />
          </Button>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleResetView}
            className="h-8 w-8 p-0"
          >
            <Maximize className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* Properties panel */}
      {selectedNode && !readOnly && (
        <div className="w-64 border-l border-ra-border bg-ra-light p-4">
          <h4 className="text-sm font-medium text-ra-text mb-3">节点属性</h4>
          <div className="space-y-3">
            <div>
              <label className="text-xs text-ra-text-secondary">类型</label>
              <p className="text-sm text-ra-text mt-1">
                {currentWorkflow.nodes.find((n) => n.id === selectedNode)?.type}
              </p>
            </div>
            <div>
              <label className="text-xs text-ra-text-secondary">标签</label>
              <input
                type="text"
                value={currentWorkflow.nodes.find((n) => n.id === selectedNode)?.label || ""}
                onChange={(e) => {
                  setCurrentWorkflow((prev) => ({
                    ...prev,
                    nodes: prev.nodes.map((n) =>
                      n.id === selectedNode ? { ...n, label: e.target.value } : n
                    ),
                  }));
                }}
                className="w-full mt-1 px-3 py-1.5 text-sm rounded border border-ra-border bg-ra-base text-ra-text focus:outline-none focus:ring-1 focus:ring-ra-accent"
              />
            </div>
            <div>
              <label className="text-xs text-ra-text-secondary">位置</label>
              <p className="text-sm text-ra-text mt-1">
                x: {Math.round(currentWorkflow.nodes.find((n) => n.id === selectedNode)?.x || 0)},
                y: {Math.round(currentWorkflow.nodes.find((n) => n.id === selectedNode)?.y || 0)}
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
