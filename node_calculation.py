import pandas as pd
import dash
from dash import html
import pandas as pd
import write_DB

#ノードを定義 
class TreeNode:
    def __init__(self, id, contribution, evaluation,type):
        self.id = id
        self.contribution = contribution
        self.evaluation = evaluation
        self.type=type
        self.children = []
        self.parent = None
    def add_child(self, child_node):
        self.children.append(child_node)
        child_node.parent = self
    def is_leaf(self):
        return len(self.children) == 0
    
#表示する
def print_tree(node, indent=""):
    if node is None:
        return  # ノードがNoneの場合は再帰を終了する
    print(f"{indent}ID:{node.id}, 貢献度: {node.contribution}, 評価点: {node.evaluation},タイプ:{node.type}")
    for child in node.children:
        print_tree(child, indent + "  ")
        
#木構造の作成
def create_tree(pname,parent_node_value, parent_node=None):
    pid=write_DB.w_project(pname)
    nid=write_DB.check_nid(pname,parent_node_value)
    if nid !='none':
        child_nodes=write_DB.make_child(nid)
        if parent_node is None:
            parent_node = TreeNode(parent_node_value, 1, 0,'REQ')
        for row in child_nodes:
            name=write_DB.check_name(row,pid)
            id= name
            contribution=write_DB.check_contribution(pname,name)
            if contribution=='H':
                new_contribution=3
            elif contribution=='M':
                new_contribution=2
            elif contribution=='L':
                new_contribution=1
            else:
                new_contribution=0
            child_evaluation = write_DB.check_aim(pname,name)
            type=write_DB.check_type(name)
            if child_evaluation != None:
                    child_evaluation = child_evaluation
            else:
                child_evaluation = 1
            node = TreeNode(id, new_contribution, child_evaluation,type)
            parent_node.add_child(node)
            create_tree(pname, id, node)
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
                    node.add_child(grandchild)  # 親の親ノードとの関係を修正
    node.children = updated_children
    # 貢献度が0の親ノードを削除し、その子ノードを親の親ノードに関連付ける
    if node.contribution == 0 and not any(child.contribution != 0 for child in node.children):
        return None
    else:
        #print_tree(node)
        return node
#計算
def calculate_achievement(node):
    if node.is_leaf():
        return float(node.evaluation) *100
    else:
        # 子ノードの達成度と貢献度を考慮して親ノードの達成度を計算
        total_numerator = 0
        total_denominator = 0
        for child in node.children:
            child_achievement = calculate_achievement(child)
            total_numerator += child_achievement * float(child.contribution)
            total_denominator += child.contribution
        # 貢献度が0の場合を考慮して分母が0でないことを確認してから達成度を計算
        if total_denominator == 0:
            return 0
        achievement = total_numerator / total_denominator
        return achievement

# ツリー表示用の関数
def tree_display(node,indent=""):
    if node is None:
        return None
    tree = html.Div([
                    html.P(f"{indent}{node.id}")])
    if node.type=='IMP':
        tree = html.Div([
            html.P(f"{indent}{node.contribution}{indent}{node.id}",style = {'color': 'Green'})
        ])
    
    elif node.type=='ACT':
        tree = html.Div([
            html.P(f"{indent}{node.contribution}{indent}{node.id}",style = {'color': 'orange'})
        ])
    if node.children:
        children = [tree_display(child,indent + "　") for child in node.children]
        tree.children.append(html.Div(children))
    
    return tree

#木構造を作成
def make_tree(pname,root_node_id):
    root_node = create_tree(pname,root_node_id)
    if root_node !='none':
        updated_root = remove_zero_contribution(root_node)
    else:
        updated_root='none'
    return updated_root