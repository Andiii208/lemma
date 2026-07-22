import { useState, useEffect, useCallback } from 'react';
import { Folder, File, ChevronRight, ChevronDown, RefreshCw } from 'lucide-react';
import ReactMarkdown from 'react-markdown';

interface FileBrowserProps {
  workDir: string | null;
}

interface TreeNode {
  name: string;
  path: string;
  isDirectory: boolean;
  children?: TreeNode[];
  isExpanded?: boolean;
  isLoading?: boolean;
}

export default function FileBrowser({ workDir }: FileBrowserProps) {
  const [tree, setTree] = useState<TreeNode[]>([]);
  const [selectedFile, setSelectedFile] = useState<string | null>(null);
  const [fileContent, setFileContent] = useState<string | null>(null);

  const loadDirectory = useCallback(async (dirPath: string): Promise<TreeNode[]> => {
    if (!window.lemmaAPI) return [];
    const entries = await window.lemmaAPI.listDirectory(dirPath, workDir ?? undefined);
    return entries
      .filter((entry) => !entry.name.startsWith('.') && entry.name !== 'node_modules')
      .sort((nodeA, nodeB) => {
        if (nodeA.isDirectory !== nodeB.isDirectory) return nodeA.isDirectory ? -1 : 1;
        return nodeA.name.localeCompare(nodeB.name);
      })
      .map((entry) => ({
        name: entry.name,
        path: entry.path,
        isDirectory: entry.isDirectory,
        isExpanded: false,
        isLoading: false,
      }));
  }, [workDir]);

  useEffect(() => {
    if (workDir) void loadDirectory(workDir).then((nodes) => setTree(nodes));
  }, [workDir, loadDirectory]);

  useEffect(() => {
    if (!workDir || !window.lemmaAPI?.watchDirectory) return;
    window.lemmaAPI.watchDirectory(workDir);
    const unsubscribe = window.lemmaAPI.onFileChanged(() => {
      void loadDirectory(workDir).then((nodes) => setTree(nodes));
    });
    return () => {
      unsubscribe();
      window.lemmaAPI?.unwatchDirectory();
    };
  }, [workDir, loadDirectory]);

  const toggleDirectory = async (node: TreeNode, _depth: number) => {
    if (!node.isDirectory) {
      setSelectedFile(node.path);
      const result = await window.lemmaAPI?.readFile(node.path, workDir ?? undefined);
      setFileContent(result?.content || `无法读取: ${result?.error}`);
      return;
    }

    // Toggle expand/collapse
    setTree((prevTree) => updateTreeNode(prevTree, node.path, (treeNode) => {
      if (treeNode.isExpanded) {
        return { ...treeNode, isExpanded: false };
      }
      return { ...treeNode, isExpanded: true, isLoading: !treeNode.children };
    }));

    if (!node.children) {
      const children = await loadDirectory(node.path);
      setTree((prevTree) => updateTreeNode(prevTree, node.path, (treeNode) => ({
        ...treeNode,
        children,
        isLoading: false,
        isExpanded: true,
      })));
    }
  };

  const handleRefresh = async () => {
    if (workDir) {
      const newTree = await loadDirectory(workDir);
      setTree(newTree);
    }
  };

  const renderNode = (node: TreeNode, depth: number) => (
    <div key={node.path}>
      <button
        onClick={() => toggleDirectory(node, depth)}
        aria-expanded={node.isDirectory ? node.isExpanded : undefined}
        className={`flex items-center gap-1 w-full px-2 py-1 text-xs hover:bg-bg-tertiary rounded transition-colors ${
          selectedFile === node.path ? 'bg-accent-soft text-accent' : ''
        }`}
        style={{ paddingLeft: `${depth * 16 + 8}px` }}
      >
        {node.isDirectory && (
          node.isLoading ? (
            <RefreshCw size={12} className="animate-spin text-text-muted" />
          ) : node.isExpanded ? (
            <ChevronDown size={12} className="text-text-muted" />
          ) : (
            <ChevronRight size={12} className="text-text-muted" />
          )
        )}
        {node.isDirectory ? (
          <Folder size={14} className="text-amber-500" />
        ) : (
          <File size={14} className="text-text-muted" />
        )}
        <span className="truncate">{node.name}</span>
      </button>

      {node.isDirectory && node.isExpanded && node.children?.map((child) =>
        renderNode(child, depth + 1)
      )}
    </div>
  );

  return (
    <div className="flex h-full">
      {/* 文件树 */}
      <div className="w-64 border-r border-border overflow-y-auto">
        <div className="flex items-center justify-between px-3 py-2 border-b border-border">
          <span className="text-xs font-semibold text-text-secondary">文件浏览器</span>
          <button onClick={handleRefresh} className="text-text-muted hover:text-text-secondary">
            <RefreshCw size={12} />
          </button>
        </div>
        <div className="py-1">
          {tree.length === 0 ? (
            <p className="px-3 py-4 text-xs text-text-muted text-center">
              {workDir ? '空目录' : '请先选择工作目录'}
            </p>
          ) : (
            tree.map((node) => renderNode(node, 0))
          )}
        </div>
      </div>

      {/* 文件内容 */}
      <div className="flex-1 overflow-auto">
        {fileContent !== null ? (
          selectedFile?.endsWith('.md') ? (
            <div className="p-4 prose prose-sm prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  a({ href, children, ...props }) {
                    return (
                      <a
                        {...props}
                        href={href}
                        onClick={(event) => {
                          event.preventDefault();
                          if (href) void window.lemmaAPI?.openExternal(href);
                        }}
                      >
                        {children}
                      </a>
                    );
                  },
                }}
              >
                {fileContent}
              </ReactMarkdown>
            </div>
          ) : (
            <pre className="p-4 text-xs font-mono whitespace-pre-wrap text-text-secondary">
              {fileContent}
            </pre>
          )
        ) : (
          <div className="flex items-center justify-center h-full text-text-muted text-xs">
            点击文件查看内容
          </div>
        )}
      </div>
    </div>
  );
}

function updateTreeNode(
  nodes: TreeNode[],
  targetPath: string,
  updater: (node: TreeNode) => TreeNode
): TreeNode[] {
  return nodes.map((node) => {
    if (node.path === targetPath) return updater(node);
    if (node.children) {
      return { ...node, children: updateTreeNode(node.children, targetPath, updater) };
    }
    return node;
  });
}
