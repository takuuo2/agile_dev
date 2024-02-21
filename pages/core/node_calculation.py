import pandas as pd
import dash
from dash import html
import pandas as pd
from. import write_db

#ノードを定義 
class TreeNode:
    def __init__(self, id, contribution, other,type):
        self.id = id
        self.contribution = contribution
        self.other = other
        self.type=type
        self.children = []
        self.parent = None
    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parent = self
    def is_leaf(self):
        return len(self.children) == 0


#木構造の作成
def create_tree(pid,parent_node_value, parent_node=None):
  aim_node=write_db.check_node(pid,parent_node_value)
  if aim_node !='none':
    child_nodes=write_db.make_child(aim_node[0])
    if parent_node is None:
      parent_node = TreeNode(parent_node_value, 1, aim_node[5],aim_node[3])
    if child_nodes != []:
      for row in child_nodes:
        id= row[1]['subchar']
        contribution=row[2]
        type=row[0]
        if type=='REQ':
          other=row[1]['statement']
        elif type == 'IMP':
          other=row[1]['description']
        else:
          other=row[1]['tolerance']  
        node = TreeNode(id, contribution, other,type)
        parent_node.add_child(node)
        create_tree(pid, id, node)
  else:
    parent_node='none'
  return parent_node


#貢献度が０のやつを抜いて作り変える
def remove_zero_contribution(node):
  if node is None:
    return None
  updated_children = []
  # 子ノードの貢献度が0でないもの、または子ノードがない場合を抽出
  for child in node.children:
    updated_child = remove_zero_contribution(child)
    if updated_child and updated_child.contribution != 0:
      updated_children.append(updated_child)
    else:
      if updated_child:
        for grandchild in updated_child.children:
          node.add_child(grandchild) 
  node.children = updated_children
  # 貢献度が0の親ノードを削除し、その子ノードを親の親ノードに関連付ける
  if node.contribution == 0 and not any(child.contribution != 0 for child in node.children):
    return None
  else:
    return node

#木構造を作成
def make_tree(pid,root_node_id):
  root_node = create_tree(pid,root_node_id)
  if root_node !='none':
    updated_root = remove_zero_contribution(root_node)
  else:
    updated_root ='none'
  return updated_root

#表示する
def print_tree(node, indent=''):
  if node is None:
    return  
  print(f'{indent}ID:{node.id}, 貢献度: {node.contribution}, 他: {node.other},タイプ:{node.type}')
  for child in node.children:
    print_tree(child, indent + '  ')
    

#表示する際のやつ
def add_child_to_node(existing_root_node, parent_node_id, new_node_id, new_node_contribution, new_node_other, new_node_type):
  def add_child_to_specific_node(node):
    if node.id == parent_node_id:
      new_node = TreeNode(new_node_id, new_node_contribution, new_node_other, new_node_type)
      node.add_child(new_node) 
      return existing_root_node  
    for child in node.children:
      updated_child = add_child_to_specific_node(child)
      if updated_child:
        return existing_root_node
    return None
  return add_child_to_specific_node(existing_root_node)