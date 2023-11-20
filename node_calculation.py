import pandas as pd
import dash
from dash import html
import pandas as pd

default_evaluation_value = 0  # デフォルトの評価値を設定
#貢献度を数字に変える
def chenge(x):
    if x == 'H':
        return int(3)
    elif x == 'M':
        return int(2)
    elif x == 'L':
        return int(1)
    else:
        return int(0)

#ノードを定義 
class TreeNode:
    def __init__(self, id, contribution, evaluation):
        self.id = id
        self.contribution = contribution
        self.evaluation = evaluation
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
    #print(f"{indent}ID:{node.id}, 貢献度: {node.contribution}, 評価点: {node.evaluation}")
    for child in node.children:
        print_tree(child, indent + "  ")

# ツリー表示用の関数
def tree_display(node,name, indent=""):
    e_base = '保守性_DB.xlsx'
    df_ar = pd.read_excel(name+'_'+e_base, sheet_name=['architecture'])
    df_re = pd.read_excel(name+'_'+e_base, sheet_name=['request'])
    if node is None:
        return None
    tree = html.Div([
                    html.P(f"{indent}{node.id}")])
    for row in df_ar['architecture'].values:
        if row[3]==node.id:
            tree = html.Div([
                html.P(f"{indent}{node.contribution}{indent}{node.id}",style = {'color': 'Green'})
            ])
    for row in df_re['request'].values:
        if row[3]==node.id:
            tree = html.Div([
                html.P(f"{indent}{node.contribution}{indent}{node.id}",style = {'color': 'orange'})
            ])
    
    
    if node.children:
        children = [tree_display(child, name,indent + "　") for child in node.children]
        tree.children.append(html.Div(children))
    
    return tree

# Excelファイルから木構造を作成する関数
def create_tree_from_excel(excel_file, architecture_sheet_name, request_sheet_name, parent_node_value, parent_node=None):
    architecture_df = pd.read_excel(excel_file, sheet_name=architecture_sheet_name)
    request_df = pd.read_excel(excel_file, sheet_name=request_sheet_name)
    child_nodes_df = architecture_df[architecture_df['親'] == parent_node_value]
    if parent_node is None:
        parent_node = TreeNode(parent_node_value, 1, 0)
    for index, row in child_nodes_df.iterrows():
        if row['親'] == parent_node_value :
            id = row['実現手法']
            contribution = chenge(row['貢献度'])
            child_value = row['実現手法']
            child_evaluation = request_df.loc[request_df['名称'] == child_value, '目標値'].values
            if len(child_evaluation) > 0:
                child_evaluation = child_evaluation[0]
            else:
                child_evaluation = default_evaluation_value 
            node = TreeNode(id, contribution, child_evaluation+1.0)
            parent_node.add_child(node)
            create_tree_from_excel(excel_file, architecture_sheet_name, request_sheet_name, id, node)
    # requestのシートからも子ノードを探して追加する
    for index, row in request_df.iterrows():
        if row['親'] == parent_node_value :
            id = row['名称']
            contribution = chenge(row['貢献度'])
            child_value = row['名称']
            child_evaluation = row['目標値']
            node = TreeNode(id, contribution, child_evaluation)
            if parent_node is None:
                parent_node = node
            else:
                parent_node.add_child(node)
            create_tree_from_excel(excel_file, architecture_sheet_name, request_sheet_name, id, node)  
    #print_tree(parent_node)
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
        print_tree(node)
        return node

#計算
def calculate_achievement(node):
    if node.is_leaf():
        return node.evaluation *100
    else:
        # 子ノードの達成度と貢献度を考慮して親ノードの達成度を計算
        total_numerator = 0
        total_denominator = 0
        for child in node.children:
            child_achievement = calculate_achievement(child)
            total_numerator += child_achievement * child.contribution
            total_denominator += child.contribution
        # 貢献度が0の場合を考慮して分母が0でないことを確認してから達成度を計算
        if total_denominator == 0:
            return 0
        achievement = total_numerator / total_denominator
        return achievement
    
#木構造を作成
def make_tree(excel_file, architecture_sheet_name, request_sheet_name, root_node_id):
    root_node = create_tree_from_excel(excel_file, architecture_sheet_name, request_sheet_name, root_node_id)
    updated_root = remove_zero_contribution(root_node)
    return updated_root
