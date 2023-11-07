import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import ClientsideFunction, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto
import sqlite3
import json
import re
from collections import deque
import pandas as pd
import numpy as np
import plotly.express as px
import dash_mantine_components as dmc
import plotly.graph_objs as go
import networkx as nx
from openpyxl import Workbook, load_workbook
from queue import Queue
import ppp
import os
from datetime import datetime
import openpyxl

app = dash.Dash(external_stylesheets=[dbc.themes.FLATLY])
e_base = '保守性_DB.xlsx'
e_seet1 = 'SQuaRE'
e_seet2 = 'category'
e_seet3 = 'maintainability'
e_seet4 = 'architecture'
e_seet5 = 'request'


# 品質主特性のプルダウン作成 f_name='ファイル名',s_name='シート名'
def pull_model(f_name, s_name):
    drop_down_normalize = []
    df = pd.read_excel(f_name, sheet_name=[s_name])
    for row in df[s_name].values:
        if row[1] == '保守性':
            drop_down_normalize += [
                {
                    'label': row[1],
                    'value': row[0],
                    'title': row[2]
                }
            ]
        else:
            drop_down_normalize += [
                {
                    'label': row[1],
                    'value': row[0],
                    'title': row[2],
                    'disabled': True,
                }
            ]
    return drop_down_normalize

#カテゴリの重要度のプルダウンデータ
def select_data(x):
    data = [
        {'label': '重要度：高', 'value': 'H'},
        {'label': '重要度：中', 'value': 'M'},
        {'label': '重要度：低', 'value': 'L'}, 
        {'label': '重要度：不要', 'value': 'N'}
        ]
    return data
#重要度変換
def chenge(x):
    if x == 'H':
        return int(3)
    elif x == 'M':
        return int(2)
    elif x == 'L':
        return int(1)
    else:
        return int(0)


def insert_line_breaks(text):
    delimiters = ['[', '〇', '×', '・']
    for delimiter in delimiters:
        text = text.replace(delimiter, '￥￥' + delimiter)
    delimiters = ['￥￥']
    pattern = '|'.join(map(re.escape, delimiters))
    parts = re.split(pattern, text)
    if parts[0] == '':
        parts.pop(0)
    for i in range(len(parts) - 1):
        parts.insert(2 * i + 1, html.Br())
    return parts


#木構造
def make_tree(file_name,target):
    # グラフの生成（ここではNetworkXライブラリを使用）
    input_list=[]
    second_list=[target]
    f_list=[]
    df_ar = pd.read_excel(file_name, sheet_name=[e_seet4])
    df_re = pd.read_excel(file_name, sheet_name=[e_seet5])
    for row in df_ar[e_seet4].values:
        if row[8] == target :
            input_list+=[(target,row[3])]
            second_list+=[row[3]]


    for row in df_re[e_seet5].values:
        if row[1] == target:
            if row[7]==target:
                input_list+=[(target,row[3])]
                second_list +=[row[3]]
            else:
                for b in df_ar[e_seet4].values:
                    if row[7]==b[3]:
                        input_list+=[(row[7],row[3])]
                        
    print(input_list)
    print(second_list)
    G = nx.Graph()
    G.add_edges_from(input_list)
    #G.add_edges_from([(1, 2), (1, 3), (1, 4), (2, 5), (3, 6)])
    # bipartite_layoutを使用してノードをかぶらないように配置
    pos = nx.bipartite_layout(G, second_list, align='horizontal')
    #pos = nx.bipartite_layout(G, [1,2,3,4], align='horizontal')
    # ノードの位置を計算して左から右に広がるように配置
    max_y = max(y for x, y in pos.values())
    print(max_y)
    for node, (y, x) in pos.items():
        if node in target:
            pos[node] = (x-4, max_y *2-y+3)
        else:
            pos[node] = (x-3, (max_y+1) * 3 - (y*3))  # y座標を反転して広がりを持たせる

    # グラフデータをCytoscape用に変換
    elements = []
    for node, pos in pos.items():
        print(node)
        print(pos[0])
        print(pos[1])
        for row in df_ar[e_seet4].values:
            if node==row[3] and row[9]=='N':
                elements.append({'data': {'id': node, 'label': node},'classes':'ng', 'position': {'x': pos[0] * 100, 'y': pos[1] * 100}})
            elif node==row[3]:
                elements.append({'data': {'id': node, 'label': node},'classes':'architecture', 'position': {'x': pos[0] * 100, 'y': pos[1] * 100}})
        #df = read(e_base, e_seet5)
        for row in df_re[e_seet5].values:
            if node==row[3] and row[8]=='N':
                elements.append({'data': {'id': node, 'label': node},'classes':'ng', 'position': {'x': pos[0] * 100, 'y': pos[1] * 100}})
            elif node==row[3]:
                elements.append({'data': {'id': node, 'label': node},'classes':'request', 'position': {'x': pos[0] * 100, 'y': pos[1] * 100}})
            elif node==row[1]:
                elements.append({'data': {'id': node, 'label': node},'classes':'main', 'position': {'x': -500, 'y': 550}})

    for edge in G.edges:
        elements.append({'data': {'id': f'edge-{edge[0]}-{edge[1]}', 'source': str(edge[0]), 'target': str(edge[1])}})
    
    p=cyto.Cytoscape(
        id='cytoscape',
        layout={'name': 'preset'},  # presetレイアウトを使用
        style={'width': '100%','height': '100%'},
        elements=elements,
        stylesheet=[
            {"selector": "node",
            "style": {
                'content': 'data(label)',
                'text-halign':'center',
                'text-valign':'center',
                'text-background-padding': '4px',
                'width':'label',
                'height':'label+1',
                'shape':'round-rectangle'
                #'background-color': 'orange'
            }
            },
            {"selector": ".architecture",
            "style": {"background-color": "green"}
            },
            {"selector": ".request",
            "style": {"background-color": "orange"}
            },
            {"selector": ".main",
            "style": {"background-color": "red"}
            },
            {"selector": ".ng",
            "style": {"background-color": "gray"}
            },
            {"selector": "edge", "style": {"content": "data(weight)"}}
        ]
    )
    return p

#ログの書き込み
def update_log(file_name,sheet_name,sub,name,data_1,data_2):
    # 新しいデータ（例としてリストを使用）
    new_data = [
        [datetime.now(),sub,name,data_1,data_2]
    ]
    # 既存のExcelファイルを読み込み（存在しない場合は新しいWorkbookを作成）
    try:
        workbook = openpyxl.load_workbook(file_name)
    except FileNotFoundError:
        workbook = openpyxl.Workbook()

    # 既存のシートが存在しない場合は新しいシートを作成
    if sheet_name not in workbook.sheetnames:
        sheet = workbook.create_sheet(sheet_name)
    else:
        sheet = workbook[sheet_name]

    # 新しいデータをシートに追記
    for row_data in new_data:
        sheet.append(row_data)

    # Excelファイルに保存
    workbook.save(file_name)

    print(f'Excelファイル "{file_name}" のシート "{sheet_name}" にデータが追記されました。')
    return None

#ログを表示
def log_display(file_name,sheet_name):
    # 既存のExcelファイルを読み込む
    workbook = openpyxl.load_workbook(file_name)
    sheet = workbook[sheet_name]

    # データを取得して逆順にする
    data = []
    last_row = sheet.max_row
    for row in range(last_row, max(last_row - 5, 1), -1):
        row_data = [sheet.cell(row=row, column=col).value for col in range(1, sheet.max_column + 1)]
        data.append(row_data)
    data.reverse()  # データを逆順にする
    if sheet_name=='request_log':
        p=[
            dbc.Label('<log：品質の評価(直近5つを表示)>'),
            html.Table([
                html.Tr([html.Th('時間'), html.Th('副特性'), html.Th('名称'), html.Th('貢献度'),html.Th('目標値')]),  # カラム名を設定
                *[
                    html.Tr([html.Td(str(cell) if cell is not None else '') for cell in row])  # ラベルを文字に変更
                    for row in data
                ]
            ])
        ]
    else:
        p=[
            dbc.Label('<log：品質の実現(直近5つを表示)>'),
            html.Table([
                html.Tr([html.Th('時間'), html.Th('副特性'), html.Th('名称'), html.Th('貢献度')]),  # カラム名を設定
                *[
                    html.Tr([html.Td(str(cell) if cell is not None else '') for cell in row])  # ラベルを文字に変更
                    for row in data
                ]
            ])
        ]
    return p



# 左側
sidebar = html.Div(
    [
        #タイトル
        dbc.Row(
            [
                html.H5('Settings',
                        style={'margin-top': '10px'}
                        )
                ],
            style={"height": "4vh"},
            className='bg-primary text-white font-italic',
            id='title1'
            ),
 
        #1つ目：プロジェクト名の入力
        dbc.Row(
            [
                dbc.Label('1 :プロジェクト名'),
                dbc.Input(id='project_name',
                          type='text',
                          placeholder='プロジェクト名を入力...',
                          valid=False,
                          className='mb-3',
                          style={
                              'width': '80%',
                              'margin-left': 40
                              }
                          )
                ]
            ),

        #2つ目：品質と特性選択   
        dbc.Row(
            [
                dbc.Label('2 :品質主特性'),
                dcc.Dropdown(
                    id='dropdown_1',
                    options=pull_model(e_base, e_seet1),
                    multi=False,
                    placeholder='品質特性を選択...',
                    disabled=True,
                    style={'width': '92%',
                           'margin-left':15
                           }
                    ),
                ]
            ),
        
        #3つ目：カテゴリ入力
        dbc.Row(
            [
                dbc.Label('3 :カテゴリ'),
                dcc.Dropdown(
                    id='dropdown_2',
                    options=[],
                    multi=False,
                    placeholder='カテゴリを選択...',
                    disabled=True,
                    style={
                        'width': '92%',
                        'margin-left':15
                        }
                    ),
                ],
            ),
        
        #3.5つ目：カテゴリでその他の場合
        dbc.Row(
            [
                dbc.Label('カテゴリ名：'),
                dcc.Input(
                    id='other-input1',
                    type='text',
                    placeholder='カテゴリ名を入力...',
                    style={
                        'width': '94%',
                        'margin-left': 10
                        }
                    ),
                dbc.Label('モジュール性：'),
                dcc.Dropdown(
                    options=select_data(1),
                    id='select_0',
                    placeholder='重要度...'
                    ),
                dbc.Label('再利用性：'),
                dcc.Dropdown(
                    options=select_data(1),
                    id='select_1',
                    placeholder='重要度...'
                    ),
                dbc.Label('解析性：'),
                dcc.Dropdown(
                    options=select_data(1), 
                    id='select_2',
                    placeholder='重要度...'
                    ),
                dbc.Label('修正性：'),
                dcc.Dropdown(
                    options=select_data(1),
                    id='select_3',
                    placeholder='重要度...'
                    ),
                dbc.Label('試験性：'),
                dcc.Dropdown(
                    options=select_data(1),
                    id='select_4',
                    placeholder='重要度...'
                    ),
                html.Button(
                    '更新',
                    id='button-ex',
                    ),
                ],
            style={'display': 'none'},
            id='category_other',
            ),

        #4つ目：副特性表示    
        dbc.Row(
            [
                dbc.Label('4 :品質副特性'),
                html.Div(
                    dcc.RadioItems(
                        options=[
                            {
                                'label': html.Div(['モジュール性'], style={'color': 'MediumTurqoise'}),
                                'value': 'モジュール性',
                                },
                            {
                                'label': html.Div(['再利用性'], style={'color': 'MediumTurqoise'}),
                                'value': '再利用性',
                                },
                            {
                                'label': html.Div(['解析性'], style={'color': 'MediumTurqoise', }),
                                'value': '解析性',
                                },
                            {
                                'label': html.Div(['修正性'], style={'color': 'MediumTurqoise', }),
                                'value': '修正性',
                                },
                            {
                                'label': html.Div(['試験性'], style={'color': 'MediumTurqoise', }),
                                'value': '試験性',
                                },
                            ], 
                        id='sub-characteristic',
                        labelStyle={
                            "display": "flex",
                            "align-items": "center",
                            'width': '90%',
                            'margin-left': 20,
                            'background-color':'white',
                            },
                       
                        ),
                ),
            ],  
        ),

        #5つ目：要求文
        dbc.Row(
            [
                dbc.Label('5 :要求'),
                dcc.Dropdown(
                    id='dropdown_3',
                    options=[],
                    multi=False,
                    placeholder='要求文を選択...',
                    style={
                        'width': '94%',
                        'margin-left': 10,
                        'fontSize': 11
                        }
                    ),
            ],
        ),

        #6つ目：目標と達成度のグラフ        
        dbc.Row(
            [
                dbc.Label('6  :進捗'),
                html.Button('進捗確認',
                            id='check',
                            style={
                                'width': '30%',
                                'margin-left': '70%',
                                'background-color':'white',
                                }),
                html.Div(id='out_data')

                ],
            ),
        ]
    )

#右側
content = html.Div(
    [
        #タイトル
        dbc.Row(
            [
                html.H5('quality condition model',
                        style={'margin-top': '10px'}),
            ],
            style={"height": "4vh"},
            className='bg-secondary text-white font-italic',
        ),
        #一つ目のタブ
        dbc.Tabs(
            [
                dbc.Tab(
                    label='品質の実現',
                    tab_id='tab-1',
                    active_label_style={'color': 'red'},
                    children=[
                        dbc.Label('品質を実現させるための手法'),
                        dbc.Row(
                            [
                                html.Div(id='ar_tab'),
                                 ], 
                            style={"height": "65vh",'border': '3px solid #00FF00'},
                            )
                        ]
                    ),
 
                dbc.Tab(label='品質の評価',
                        tab_id='tab-2',
                        active_label_style={'color': 'red'},
                        children=[
                            dbc.Label('品質の評価方法'),
                            dbc.Row(
                                [
                                    html.Div(id='re_tab'),
                                    ], 
                                    style={"height": "65vh",'border': '3px solid #fed9a6'},
                                    )
                                ]
                        ),
                dbc.Tab(label='品質状態モデル', 
                        tab_id='tab-3',
                        active_label_style={'color': 'red'},
                        children=[
                            dbc.Label('品質状態モデル'),
                            dbc.Row(
                                [
                                    html.Div(id='model_tab'),
                                    dbc.Col(id='model_tree',width=9),
                                    dbc.Col(id='model_example',width=3)
                                    ], 
                                style={"height": "65vh",'border': '3px solid #b3cde3'},
                                )
                            ]
                        ),
            ],
            id="tabs",
            active_tab="",
        ),

        #木構造
        dbc.Row(
            [   
            dbc.Col(
                id='show_tree_architecture',
                ),
            dbc.Col(
                id='show_tree_request',
                ),
            ],
            style={"height": "35vh"}
            ),
        ]
    )

#レイアウト
app.layout = dbc.Container(
    [
        dbc.Row(
            [   
                dbc.Col(sidebar, width=2, className='bg-light'),
                dbc.Col(content, width=10)
            ],
            style={'height': '100vh'}
        ),
    ],
    fluid=True
)


#コールバック処理
# コールバックを作成_1 :project name⇒2:SQuaRE quality modelの制限
@app.callback(
    Output('dropdown_1', 'disabled'),
    Input('project_name', 'value')
)
def disable_input_1(input1_value):
    return not input1_value

# コールバックを作成_2:SQuaRE quality model⇒3:Category制限
@app.callback(
    Output('dropdown_2', 'options'),
    Output('dropdown_2','disabled'),
    Input('dropdown_1', 'value'),
    Input('button-ex', 'n_clicks'),
    State('project_name', 'value'),
    State('other-input1','value'),
    State('select_0','value'),
    State('select_1','value'),
    State('select_2','value'),
    State('select_3','value'),
    State('select_4','value')
)
def disable_input_2(input1_value,input2,name,values, values0,values1, values2, values3, values4):
    if input1_value is None or input1_value == '':
        return dash.no_update
        
    else:
        node = pull_make(e_base, e_seet2, 2, 2,  input1_value)
        x = [{'label': 'その他', 'value': 'その他'}]
        node += x
        
        new_file_path =name+'_保守性_DB.xlsx'
        # ファイルが存在するか確認
        if os.path.isfile(new_file_path):
            None
        else:
            # 新しいデータ
            new_data = {
                'Column1': ['New Value 1', 'New Value 2'],
            }
            # 新しいデータをDataFrameに変換
            df_new = pd.DataFrame(new_data)
            df_new.to_excel(new_file_path, index=False)
            all_sheets = {}
            xls = pd.ExcelFile(e_base)
            # 全てのシートを読み込んで辞書に格納
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name=sheet_name)
                all_sheets[sheet_name] = df
            with pd.ExcelWriter(new_file_path, engine='openpyxl', mode='w') as writer:
                # 辞書内の各シートを新しいExcelファイルに書き込む
                for sheet_name, df in all_sheets.items():
                    df.to_excel(writer,sheet_name=sheet_name, index=False)
            print('来てる')
        if input2 is not None:
            existing_data = pd.read_excel(e_base, sheet_name=[e_seet2])
            row_count=0
            for row in existing_data[e_seet2].values:
                row_count=row_count+1
            id = row_count + 1
            df4 = pd.DataFrame([[id,'4.2.7',values, values0,values1, values2, values3, values4]])
            with pd.ExcelWriter(e_base, mode='a', engine='openpyxl', if_sheet_exists='overlay') as writer:
                df4.to_excel(writer, sheet_name=e_seet2, index=False, header=False, startrow=row_count+1)
                print(e_base,'更新完了')
            node = pull_make2(e_base, e_seet2, 2, 2)
            x = [{'label': 'その他', 'value': 'その他'}]
            node += x
        return node,False
    
def pull_make(f_name, s_name, label, value,  conditions):
    drop_down_normalize = []
    df = pd.read_excel(f_name, sheet_name=[s_name])
    for row in df[s_name].values:
        if row[1] == conditions:
            drop_down_normalize += [
                {
                    'label': row[label],
                    'value': row[value],
                }
            ]
    return drop_down_normalize

def pull_make2(f_name, s_name, label, value):
    drop_down_normalize = []
    df =pd.read_excel(f_name, sheet_name=[s_name])
    for row in df[s_name].values:
            drop_down_normalize += [
                {
                    'label': row[label],
                    'value': row[value],
                }
            ]
    return drop_down_normalize

# コールバックを作成_3:Categoryでその他を選択したとき
@app.callback(
    Output('category_other', 'style'),
    Input('dropdown_2', 'value'),
    Input('button-ex', 'n_clicks'),
)
def disable_input_3(input1_value,n_click):
    if input1_value == 'その他' and  n_click is None:
        style={'backgroundColor': 'LightBlue'}
        return style
    else:
        style={'display': 'none'}
        return style

# コールバックを作成_3:Category⇒4 :Sub-characteristic,6 :Goals and Achievements
@app.callback(
    Output('sub-characteristic', 'options'),
    Output('out_data','children'),
    Input('dropdown_2', 'value'),
    Input('check','n_clicks'),
    State('project_name', 'value'),

    prevent_initial_call=True
)
def disable_input_5(input1_value,click,name):
    if (input1_value is None or input1_value == '') :
        options=[]
        return options,dash.no_update 
    elif click is not None or click != '':
        new_file=name+'_'+e_base
        df = pd.read_excel(new_file, sheet_name=[e_seet2])
        options=[]
        list=('H','M','L','N')
        color_list=('red','orange','LightGreen','MediumTurqoise')
        font_list=(20,20,20,20)
        x=0
        name_in=[]
        y=[]
        z=[]
        for row in df[e_seet2].values:
            if row[2] == input1_value:
                for i in list:
                    if row[3] ==i:
                        options +={
                            'label': html.Div(['モジュール性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': 'モジュール性',
                            },
                        name_in +=['モジュール性']
                        y+=row[3]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, 'モジュール性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[4] ==i:
                        options +={
                            'label': html.Div(['再利用性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '再利用性',
                            },
                        name_in +=['再利用性']
                        y+=row[4]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '再利用性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[5] ==i:
                        options +={
                            'label': html.Div(['解析性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '解析性',
                            },
                        name_in +=['解析性']
                        y+=row[5]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '解析性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[6] ==i:
                        options +={
                            'label': html.Div(['修正性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '修正性',
                            },
                        name_in +=['修正性']
                        y+=row[6]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '修正性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[7] ==i:
                        options +={
                            'label': html.Div(['試験性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '試験性',
                            },
                        name_in +=['試験性']
                        y+=row[7]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '試験性')
                        z += [ppp.calculate_achievement(root_node)]
                    x=x+1
                sum=0
                for i in range(5):
                    sum=sum+chenge(y[i])
                aim0=chenge(y[0])/sum*100
                aim1=chenge(y[1])/sum*100
                aim2=chenge(y[2])/sum*100
                aim3=chenge(y[3])/sum*100
                aim4=chenge(y[4])/sum*100
                sum_num=0.0
                for i in range(5):
                    sum_num=sum_num+z[i]
                if sum_num !=0.0:
                    aim_n0=z[0]/sum_num*100
                    aim_n1=z[1]/sum_num*100
                    aim_n2=z[2]/sum_num*100
                    aim_n3=z[3]/sum_num*100
                    aim_n4=z[4]/sum_num*100
                else:
                    aim_n0=0.0
                    aim_n1=0.0
                    aim_n2=0.0
                    aim_n3=0.0
                    aim_n4=0.0
                data=[
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim0,aim_n0],
                        name=name_in[0]
                        ),
                    
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim1,aim_n1],
                        name=name_in[1]
                        ),
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim2,aim_n2],
                        name=name_in[2]
                        ),
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim3,aim_n3],
                        name=name_in[3]
                        ),
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim4,aim_n4],
                        name=name_in[4]
                        ),
                    ]
                p=dcc.Graph(
                    id='stacked-bar-chart',
                    figure={
                        'data': data,
                        'layout': go.Layout(
                            barmode='stack',  # 積み上げ設定
                            yaxis={'title': '割合（%）'},
                            bargroupgap=0.1,  # グループ間の間隔
                            margin={'l': 35, 'r': 20, 't': 10, 'b': 20}
                            )
                        },
                    style={'width': '100%', 'height': '330px'}
                    )
        return options,p
    else:
        new_file=name+'_'+e_base
        df = pd.read_excel(new_file, sheet_name=[e_seet2])
        options=[]
        list=('H','M','L','N')
        color_list=('red','orange','LightGreen','MediumTurqoise')
        font_list=(20,20,20,20)
        x=0
        name_in=[]
        y=[]
        z=[]
        for row in df[e_seet2].values:
            if row[2] == input1_value:
                for i in list:
                    if row[3] ==i:
                        options +={
                            'label': html.Div(['モジュール性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': 'モジュール性',
                            },
                        name_in +=['モジュール性']
                        y+=row[3]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, 'モジュール性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[4] ==i:
                        options +={
                            'label': html.Div(['再利用性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '再利用性',
                            },
                        name_in +=['再利用性']
                        y+=row[4]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '再利用性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[5] ==i:
                        options +={
                            'label': html.Div(['解析性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '解析性',
                            },
                        name_in +=['解析性']
                        y+=row[5]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '解析性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[6] ==i:
                        options +={
                            'label': html.Div(['修正性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '修正性',
                            },
                        name_in +=['修正性']
                        y+=row[6]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '修正性')
                        z += [ppp.calculate_achievement(root_node)]
                    if row[7] ==i:
                        options +={
                            'label': html.Div(['試験性'], style={'color': color_list[x],'font-size': font_list[x]}),
                            'value': '試験性',
                            },
                        name_in +=['試験性']
                        y+=row[7]
                        root_node = ppp.create_tree_from_excel(new_file, e_seet4, e_seet5, '試験性')
                        z += [ppp.calculate_achievement(root_node)]
                    x=x+1
                sum=0
                for i in range(5):
                    sum=sum+chenge(y[i])
                aim0=chenge(y[0])/sum*100
                aim1=chenge(y[1])/sum*100
                aim2=chenge(y[2])/sum*100
                aim3=chenge(y[3])/sum*100
                aim4=chenge(y[4])/sum*100
                sum_num=0.0
                for i in range(5):
                    sum_num=sum_num+z[i]
                if sum_num !=0.0:
                    aim_n0=z[0]/sum_num*100
                    aim_n1=z[2]/sum_num*100
                    aim_n2=z[2]/sum_num*100
                    aim_n3=z[3]/sum_num*100
                    aim_n4=z[4]/sum_num*100
                else:
                    aim_n0=0.0
                    aim_n1=0.0
                    aim_n2=0.0
                    aim_n3=0.0
                    aim_n4=0.0
                data=[
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim0,aim_n0],
                        name=name_in[0]
                        ),
                    
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim1,aim_n1],
                        name=name_in[1]
                        ),
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim2,aim_n2],
                        name=name_in[2]
                        ),
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim3,aim_n3],
                        name=name_in[3]
                        ),
                    go.Bar(
                        x=['目標', '達成度'],
                        y=[aim4,aim_n4],
                        name=name_in[4]
                        ),
                    ]
                p=dcc.Graph(
                    id='stacked-bar-chart',
                    figure={
                        'data': data,
                        'layout': go.Layout(
                            barmode='stack',  # 積み上げ設定
                            yaxis={'title': '割合（%）'},
                            bargroupgap=0.1,  # グループ間の間隔
                            margin={'l': 35, 'r': 20, 't': 10, 'b': 20}
                            )
                        },
                    style={'width': '100%', 'height': '330px'}
                    )
        return options,p

#コールバックを作成_4 :Sub-characteristic⇒5 :Request item list
@app.callback(
    Output('dropdown_3', 'options'),
    Output('tabs','active_tab'),
    Input('sub-characteristic', 'value'),
)
def up_drop(input_value):
    options = []
    df = pd.read_excel(e_base, sheet_name=[e_seet5])
    #print(input_value)
    for row in df[e_seet5].values:
        if row[1] == input_value:
            options += [
                {
                    'label': row[2],
                    'value': row[2],
                }
            ]
    options += [{'label': 'その他', 'value': 'その他'}]
    count=0
    new_options=[]
    for x in options:
        for y in new_options:
            if x==y:
                count=count+1
        if count==0:
            new_options+=[x]
        count=0    
    return new_options,''

#コールバックを作成_5 :Request item list⇒右上
@app.callback(
    Output('ar_tab', 'children'),
    Output('re_tab', 'children'),
    Input('dropdown_3', 'value'),
    State('sub-characteristic', 'value'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def up_data(input_value,input2_value,input3_value):
    new_file=input3_value+'_'+e_base
    df_request = pd.read_excel(new_file, sheet_name=[e_seet5])
    df_architecture = pd.read_excel(new_file, sheet_name=[e_seet4])
    ar_tabs = []
    re_tabs = []
    if input_value !='その他':
        for row in df_request[e_seet5].values:
            if row[2] == input_value: 
                tab_content = dbc.Tab(
                        label=row[3],
                        tab_id=row[3],
                        active_label_style={'color': 'red'},
                        children=[
                            dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<説明>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                html.P(
                                                        insert_line_breaks(row[4]),
                                                        id='re_exa',
                                                        ), 
                                                
                                                    ],
                                                width=11,
                                            
                                                ),
                                            html.Hr(),
                                            ],
                                        ),
                            dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<測定機能>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                    html.P(
                                                            insert_line_breaks(row[5]),
                                                            id='re_ex',
                                                            ), 
                                                    ],
                                                width=6,
                                                ),
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<測定A>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),     
                                                    dbc.Label(
                                                        '<測定B>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),     
                                                    ],
                                                width=1,
                                                ),
                                            dbc.Col(
                                                [
                                                    html.P(
                                                            '他研究A',
                                                            id='re_a',
                                                            ),      
                                                    html.P(
                                                            '他研究B',
                                                            id='re_b',
                                                            ), 
                                                    ],
                                                width=4,
                                                ),
                                            html.Hr(),
                                            ],
                                        ),
                            dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<Xの目標値>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                    '目標値を入力してください(0.00-1.00で入力)',
                                                    dbc.Input(
                                                         id={'type': 'input','index': row[3]},
                                                        type='number',
                                                        value=row[9],
                                                        min=0,  
                                                        max=1,  
                                                        step=0.01,
                                                        valid=False,
                                                        className='mb-3',
                                                        )
                                                    ],
                                                width=3,
                                                ),
                                            html.Hr(),
                                        ],
                                    ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        [
                                            dbc.Label(
                                                '<重要度入力>',
                                                style={'fontSize': 15, 'fontWeight': 'bold'},
                                                ),      
                                            ],
                                        className="text-center",
                                        width=1,
                                        align="center",  
                                        ),
                                    dbc.Col(
                                        [
                                            dcc.Dropdown(
                                                options=select_data(1),
                                                id={'type': 'dropdown','index': row[3]},
                                                placeholder='重要度...',
                                                value=row[8],
                                                ),  
                                            ],
                                        width=9,
                                        ),
                                    dbc.Col(
                                        [
                                            html.Button(
                                                '更新',
                                                id={'type': 'button','index': row[3]},
                                                style={'background-color':'red',
                                                    }
                                                ),
                                            ],
                                        width=2,
                                        ),
                                    ]
                                )
                            ],
                        )   
                re_tabs.append(tab_content)
                if row[7] !=input2_value:
                    for i in df_architecture[e_seet4].values:
                        if i[3]==row[7]:
                            tab_content = dbc.Tab(
                                label=row[7],
                                tab_id=row[7],
                                active_label_style={'color': 'red'},
                                children=[
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<基本戦略>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                html.P(
                                                        insert_line_breaks(i[1]),
                                                        id='ar_base',
                                                        ), 
                                                  
                                                    ],
                                                width=11,
                                             
                                                ),
                                            html.Hr(),
                                            ],
                                        ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<個別戦略>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                html.P(
                                                        insert_line_breaks(i[2]),
                                                        id='ar_in',
                                                        ), 
                                                  
                                                    ],
                                                width=11,
                                             
                                                ),
                                            html.Hr(),
                                            ],
                                        ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<説明>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                html.P(
                                                        insert_line_breaks(i[4]),
                                                        id='ar_exa',
                                                        ), 
                                                  
                                                    ],
                                                width=11,
                                             
                                                ),
                                            html.Hr(),
                                            ],
                                        ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<前提条件>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                html.P(
                                                        insert_line_breaks(i[5]),
                                                        id='ar_tec',
                                                        ), 
                                                  
                                                    ],
                                                width=11,
                                             
                                                ),
                                            html.Hr(),
                                            ],
                                        ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<実現例>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                html.P(
                                                        insert_line_breaks(i[6]),
                                                        id='ar_tec',
                                                        ), 
                                                  
                                                    ],
                                                width=11,
                                             
                                                ),
                                            html.Hr(),
                                            ],
                                        ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Label(
                                                        '<重要度入力>',
                                                        style={'fontSize': 15, 'fontWeight': 'bold'},
                                                        ),      
                                                    ],
                                                className="text-center",
                                                width=1,
                                                align="center",  
                                                ),
                                            dbc.Col(
                                                [
                                                    dcc.Dropdown(
                                                        options=select_data(1),
                                                        id={'type': 'dropdown','index': i[3]},
                                                        placeholder='重要度...',
                                                        value=i[9],
                                                        ),  
                                                    ],
                                                width=9,
                                                ),
                                            dbc.Col(
                                                [
                                                    html.Button(
                                                        '更新',
                                                        id={'type': 'button','index': i[3]},
                                                        style={'background-color':'red',
                                                            }
                                                        ),
                                                    ],
                                                width=2,
                                                ),
                                            ],
                                        ),

                                    ]
                                )
                    ar_tabs.append(tab_content)
    else:
        re_list=[]
        ar_list=[]
        unique_elements=[]
        for row in df_request[e_seet5].values:
            if row[1]==input2_value:
                re_list+=[row[7]]
                re_list+=[input2_value]
        for row in df_architecture[e_seet4].values:
            if row[7]==input2_value:
                ar_list+=[row[3]]
                ar_list+=[input2_value]
        #print(ar_list,re_list)
        unique_elements += set(re_list) ^ set(ar_list)
        #print(unique_elements)
        for i in unique_elements:
            for x in df_architecture[e_seet4].values:
                if i==x[3]:
                    tab_content = dbc.Tab(
                            label=i,
                            tab_id=i,
                            active_label_style={'color': 'red'},
                            children=[
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                '<基本戦略>',
                                                                style={'fontSize': 15, 'fontWeight': 'bold'},
                                                                ),      
                                                            ],
                                                        className="text-center",
                                                        width=1,
                                                        align="center",  
                                                        ),
                                                    dbc.Col(
                                                        [
                                                        html.P(
                                                                insert_line_breaks(x[1]),
                                                                id='ar_base',
                                                                ), 
                                                        
                                                            ],
                                                        width=11,
                                                    
                                                        ),
                                                    html.Hr(),
                                                    ],
                                                ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                '<個別戦略>',
                                                                style={'fontSize': 15, 'fontWeight': 'bold'},
                                                                ),      
                                                            ],
                                                        className="text-center",
                                                        width=1,
                                                        align="center",  
                                                        ),
                                                    dbc.Col(
                                                        [
                                                        html.P(
                                                                insert_line_breaks(x[2]),
                                                                id='ar_in',
                                                                ), 
                                                        
                                                            ],
                                                        width=11,
                                                    
                                                        ),
                                                    html.Hr(),
                                                    ],
                                                ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                '<説明>',
                                                                style={'fontSize': 15, 'fontWeight': 'bold'},
                                                                ),      
                                                            ],
                                                        className="text-center",
                                                        width=1,
                                                        align="center",  
                                                        ),
                                                    dbc.Col(
                                                        [
                                                        html.P(
                                                                insert_line_breaks(x[4]),
                                                                id='ar_exa',
                                                                ), 
                                                        
                                                            ],
                                                        width=11,
                                                    
                                                        ),
                                                    html.Hr(),
                                                    ],
                                                ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                '<前提条件>',
                                                                style={'fontSize': 15, 'fontWeight': 'bold'},
                                                                ),      
                                                            ],
                                                        className="text-center",
                                                        width=1,
                                                        align="center",  
                                                        ),
                                                    dbc.Col(
                                                        [
                                                        html.P(
                                                                insert_line_breaks(x[5]),
                                                                id='ar_tec',
                                                                ), 
                                                        
                                                            ],
                                                        width=11,
                                                    
                                                        ),
                                                    html.Hr(),
                                                    ],
                                                ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                '<実現例>',
                                                                style={'fontSize': 15, 'fontWeight': 'bold'},
                                                                ),      
                                                            ],
                                                        className="text-center",
                                                        width=1,
                                                        align="center",  
                                                        ),
                                                    dbc.Col(
                                                        [
                                                        html.P(
                                                                insert_line_breaks(x[6]),
                                                                id='ar_tec',
                                                                ), 
                                                        
                                                            ],
                                                        width=11,
                                                    
                                                        ),
                                                    html.Hr(),
                                                    ],
                                                ),
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            dbc.Label(
                                                                '<重要度入力>',
                                                                style={'fontSize': 15, 'fontWeight': 'bold'},
                                                                ),      
                                                            ],
                                                        className="text-center",
                                                        width=1,
                                                        align="center",  
                                                        ),
                                                    dbc.Col(
                                                        [
                                                            dcc.Dropdown(
                                                                options=select_data(1),
                                                                id={'type': 'dropdown','index': x[3]},
                                                                placeholder='重要度...',
                                                                value=x[9],
                                                                ),  
                                                            ],
                                                        width=9,
                                                        ),
                                                    dbc.Col(
                                                        [
                                                            html.Button(
                                                                '更新',
                                                                id={'type': 'button','index': x[3]},
                                                                style={'background-color':'red',
                                                                    }
                                                                ),
                                                            ],
                                                        width=2,
                                                        ),
                                                    ],
                                                ),
                                            ]
                            )
                    ar_tabs.append(tab_content)
            
    ar=dbc.Tabs(
        id='ar_tabs',
        children=ar_tabs,
        active_tab='',
    )
    re=dbc.Tabs(
        id='re_tabs',
        children=re_tabs,
        active_tab='',
    )
    return ar,re

#コールバックを作成_品質実現の更新
@app.callback(
    Output('ar_tabs', 'active_tab'),
    Output('show_tree_architecture','children'),
    Input({'type': 'button', 'index': ALL}, 'n_clicks'),
    State({'type': 'dropdown','index': ALL},'value'),
    State({'type': 'dropdown','index': ALL},'id'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def update_output(n_clicks_list,values,id,name):
    if not n_clicks_list or all(n is None for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id
    if triggered_id is not None:
        button_id = triggered_id['index']
        index_values = [item['index'] for item in id]
        df = pd.read_excel(name+'_'+e_base, sheet_name=[e_seet4])
        for a,b in zip(index_values,values):
            if a==button_id:
                for row in df[e_seet4].values:
                    if row[3]==button_id:
                        #print(a,b,button_id)
                        write_file_ar(name+'_'+e_base,button_id,b)
                        update_log(name+'_'+e_base,'architecture_log',row[8],row[3],b,'')
        return '',log_display(name+'_'+e_base,'architecture_log')

#アーキの書き込み
def write_file_ar(file_name,target_node,new_data):
    # シート名
    target_sheet_name = 'architecture'
    i=0
    #print(target_node)
    df = pd.read_excel(file_name, sheet_name=[target_sheet_name])
    for row in df[target_sheet_name].values:
        if row[3] == target_node:
            i=i+1
            break
        else:
            i=i+1     
    try:
        # 既存のExcelファイルを読み込む
        workbook = load_workbook(file_name)
        # 既存のシートにアクセスし、特定のセルを編集する
        sheet = workbook[target_sheet_name]
        target_sel='J'+str(i+1)
        sheet[target_sel] = new_data  
        #print(i)
        # Excelファイルを保存
        workbook.save(file_name)
    except Exception as e:
        print(f'エラー: {e}')

#品質活動の更新
@app.callback(
    Output('re_tabs', 'active_tab'),
    Output('show_tree_request','children'),
    Input({'type': 'button', 'index': ALL}, 'n_clicks'),
    State({'type': 'dropdown','index': ALL},'value'),
    State({'type': 'dropdown','index': ALL},'id'),
    State({'type': 'input','index': ALL},'value'),
    State({'type': 'input','index': ALL},'id'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def updata(n_clicks_list,values1,id1,value2,id2,name):
    if not n_clicks_list or all(n is None for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id
    if triggered_id is not None:
        button_id = triggered_id['index']
        #print(button_id)
        index_values = [item['index'] for item in id1]
        #print(index_values)
        #print(values1)
        index_values1 = [item['index'] for item in id2]
        #print(index_values1)
        #print(value2)
        df = pd.read_excel(name+'_'+e_base, sheet_name=[e_seet5])
        for a,b in zip(index_values,values1):
            if a==button_id:
                for c,d in zip(index_values1,value2):
                    if c==button_id:                
                        for row in df[e_seet5].values:
                            if row[3]==button_id:
                                #print(a,b,button_id,c,d)
                                write_file_re(name+'_'+e_base,button_id,b,d)
                                update_log(name+'_'+e_base,'request_log',row[1],row[3],b,d)
        return '',log_display(name+'_'+e_base,'request_log')

#要求文の書き込み
def write_file_re(file_name,target_node,new_data,new_num):
    # シート名
    target_sheet_name = 'request'
    i=0
    df = pd.read_excel(file_name, sheet_name=[target_sheet_name])
    #print(target_node)
    for row in df[target_sheet_name].values:
        if row[3] == target_node:
            i=i+1
            break
        else:
            i=i+1
    #print(i)         
    try:
        # 既存のExcelファイルを読み込む
        workbook = load_workbook(file_name) 
        # 既存のシートにアクセスし、特定のセルを編集する
        sheet = workbook[target_sheet_name]
        target_sel='I'+str(i+1)
        target_num='J'+str(i+1)
        #print(target_sel)
        sheet[target_sel] = new_data  # A1セルの内容を新しいデータに置き換える
        sheet[target_num] = new_num
        # Excelファイルを保存
        workbook.save(file_name)
    except Exception as e:
        print(f'エラー: {e}')
        

#コールバックを作成_品質状態モデル
@app.callback(
    Output('model_tab', 'children'),
    Input('dropdown_1', 'value'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def up_data(input_value,name):
    new_file=name+'_'+e_base
    df_sub = pd.read_excel(new_file, sheet_name=[e_seet3])
    sub_list=[]
    for row in df_sub[e_seet3].values:    
        tab_content = dbc.Tab(
                label=row[1],
                tab_id=row[1],
                active_label_style={'color': 'red'},
                )
        sub_list.append(tab_content)
    
    model=dbc.Tabs(
        id='model_tabs',
        children=sub_list,
        active_tab='',
    )
    return model

#コールバックを作成_品質状態モデル_tree
@app.callback(
    Output('model_tree', 'children'),
    Input('model_tabs', 'active_tab'),
    #State('cytoscape','tapNodeData'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def up_data(input_value,name):
    if input_value is not None:
        new_file=name+'_'+e_base
        print(input_value)
        #print(v1)
        return make_tree(new_file,input_value) 
    

#コールバックを作成_品質状態モデル_tree
@app.callback(
    Output('model_example', 'children'),
    Input('cytoscape','tapNodeData'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def up_data(v1,name):
    if v1 is not None:
        selected_node = v1['label']
        new_file=name+'_'+e_base
        df_ar = pd.read_excel(new_file, sheet_name=[e_seet4])
        df_re = pd.read_excel(new_file, sheet_name=[e_seet5])
        child=[]
        for row in df_ar[e_seet4].values:    
            if row[3]== selected_node:
                child = [
                        dbc.Label(
                            '<名称>',
                            style={'fontSize': 15, 'fontWeight': 'bold'}
                        ),
                        html.P(row[3],id='tree_ar_name'),
                        dbc.Label(
                            '<重要度>',
                            style={'fontSize': 15, 'fontWeight': 'bold'}
                        ),
                        dcc.Dropdown(
                            options=select_data(1),
                            id='tree_ar_dropdown',
                            placeholder='重要度...',
                            value=row[9]
                        ),
                        dbc.Input(
                            id='tree_ar_input',
                            type='number',
                            value=row[9],
                            min=0,  
                            max=1,  
                            step=0.01,
                            valid=False,
                            className='mb-3',
                            style={'display':'none'}
                        ),
                        html.Button(
                            '更新',
                            id='tree_ar_button',
                            style={'background-color':'red'}
                        ),
                        html.P(id='tree_ar_ee'),
                    ]
        for row in df_re[e_seet5].values:    
            if row[3]== selected_node:
                child = [
                        dbc.Label(
                            '<名称>',
                            style={'fontSize': 15, 'fontWeight': 'bold'}
                        ),
                        html.P(row[3],id='tree_ar_name'),
                        dbc.Label(
                            '<重要度>',
                            style={'fontSize': 15, 'fontWeight': 'bold'}
                        ),
                        dcc.Dropdown(
                            options=select_data(1),
                            id='tree_ar_dropdown',
                            placeholder='重要度...',
                            value=row[8]
                        ),
                        dbc.Label(
                            '<Xの目標値>',
                            style={'fontSize': 15, 'fontWeight': 'bold'},
                            ), 
                        dbc.Input(
                            id='tree_ar_input',
                            type='number',
                            value=row[9],
                            min=0,  
                            max=1,  
                            step=0.01,
                            valid=False,
                            className='mb-3',
                        ),
                        html.Button(
                            '更新',
                            id='tree_ar_button',
                            style={'background-color':'red'}
                        ),
                        html.P(id='tree_ar_ee'),
                    ]
        return child

@app.callback(
    Output('model_tabs','active_tab'),
    Output('tree_ar_ee','children'),
    Input('tree_ar_button','n_clicks'),
    State('tree_ar_dropdown','value'),
    State('tree_ar_name','children'),
    State('tree_ar_input','value'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def up_data(n_click,value1,value2,value3,name):
    if n_click is None :
        return dash.no_update
    else:
        print(n_click)
        print(value1)
        print(value2)
        print(value3)
        
        df_ar = pd.read_excel(name+'_'+e_base, sheet_name=[e_seet4])
        df_re = pd.read_excel(name+'_'+e_base, sheet_name=[e_seet5])
        for row in df_ar[e_seet4].values:
            if row[3]==value2:
                write_file_ar(name+'_'+e_base,row[3],value1)
                update_log(name+'_'+e_base,'architecture_log',row[8],row[3],value1,'')
                return '','更新しました。もう一度’'+row[8]+'’をおしてください'
        for row in df_re[e_seet5].values:
            if row[3]==value2:
                write_file_re(name+'_'+e_base,row[3],value1,value3)
                update_log(name+'_'+e_base,'request_log',row[1],row[3],value1,value3)
                return '','更新しました。もう一度’'+row[1]+'’をおしてください'
            
        
#サーバーを立てる
if __name__ == "__main__":
    app.run_server(debug=True)

