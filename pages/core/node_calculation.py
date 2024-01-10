import pandas as pd
import dash
from dash import html
import pandas as pd
from. import write_DB

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
def create_tree(pname,parent_node_value, parent_node=None):
    nid=write_DB.check_nid(pname,parent_node_value)
    if nid !='none':
        child_nodes=write_DB.make_child(nid)
        if parent_node is None:
            parent_node = TreeNode(parent_node_value, 1, write_DB.check_node(pname,parent_node_value)[1],'REQ')
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
                    node.add_child(grandchild) 
    node.children = updated_children
    # 貢献度が0の親ノードを削除し、その子ノードを親の親ノードに関連付ける
    if node.contribution == 0 and not any(child.contribution != 0 for child in node.children):
        return None
    else:
        #print_tree(node)
        return node

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
        #print_tree(node)
        return node
    
#表示する際のやつ
def add_child_to_node(existing_root_node, parent_node_id, new_node_id, new_node_contribution, new_node_other, new_node_type):
    """
    既存の木構造の特定の親ノードに新しい子ノードを追加する関数。
    Args:
    - existing_root_node: 既存の木構造全体のルートノード
    - parent_node_id: 新しい子ノードを追加する親ノードのID
    - new_node_id: 新しいノードのID
    - new_node_contribution: 新しいノードの貢献度
    - new_node_other: 新しいノードの他の情報
    - new_node_type: 新しいノードのタイプ
    Returns:
    - existing_root_node: 木構造全体のルートノード
    """
    def add_child_to_specific_node(node):
        if node.id == parent_node_id:
            new_node = TreeNode(new_node_id, new_node_contribution, new_node_other, new_node_type)
            node.add_child(new_node)  # 新しいノードを指定された親ノードの下に追加する

            return existing_root_node  # 木構造全体を返す

        for child in node.children:
            updated_child = add_child_to_specific_node(child)
            if updated_child:
                return existing_root_node

        return None

    return add_child_to_specific_node(existing_root_node)

    

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
            html.P(f"{indent}{node.contribution}{indent}{node.id}",style = {'color': 'orange',})
        ])
    print(type(tree))
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
   # print_tree(updated_root)
    return updated_root

#表示する
def print_tree(node, indent=""):
    if node is None:
        return  # ノードがNoneの場合は再帰を終了する
    print(f"{indent}ID:{node.id}, 貢献度: {node.contribution}, 他: {node.other},タイプ:{node.type}")
    for child in node.children:
        print_tree(child, indent + "  ")