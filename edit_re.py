import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import ClientsideFunction, Input, Output, State, MATCH, ALL
from dash.exceptions import PreventUpdate
import dash_cytoscape as cyto
import pandas as pd
import sqlite3
import plotly.graph_objs as go
import node_calculation
import re
from openpyxl import Workbook, load_workbook
from node_calculation import TreeNode

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

# カテゴリ
def dropdown_category():
    # SQLiteデータベースに接続
    conn = sqlite3.connect('QC_DB.db')
    cursor = conn.cursor()

    # テーブルからデータを取得
    cursor.execute('SELECT id, category_name FROM categories')
    data = cursor.fetchall()
    # データベースの接続を閉じる
    cursor.close()
    conn.close()
    dropdown_normalize = []
    dropdown_normalize=[{'label': str(row[1]), 'value': str(row[0])} for row in data]
    return dropdown_normalize  

#品質副特性のデータを構成
def dropdown_sub(category_num,SQuaRE_name):
    options=[]
    list=('H','M','L','N')
    color_list=('red','orange','LightGreen','MediumTurqoise')
    # SQLiteデータベースに接続
    conn = sqlite3.connect('QC_DB.db')
    cursor = conn.cursor()
    # テーブルからデータを取得
    cursor.execute('SELECT category_id, second_name,third_name,importance category_name FROM subcategories')
    data = cursor.fetchall()
    # データベースの接続を閉じる
    cursor.close()
    conn.close()
    x=0
    for i in list:
        for num in data:
            if num[3] ==i:
                if str(category_num)==str(num[0]) and SQuaRE_name==num[1]:
                    options +={
                        'label': html.Div(num[2], style={'color': color_list[x],'font-size': 20}),
                        'value': num[2],
                        },
        x=x+1
    return options

#重要度＆貢献度変換
def chenge(x):
    if x == 'H':
        return int(3)
    elif x == 'M':
        return int(2)
    elif x == 'L':
        return int(1)
    else:
        return int(0)

#グラフのデータ作成
def make_data(category_num,SQuaRE_name,new):
    new_file=new+'_'+e_base
    datas=[]
    name_in=[]
    y=[]
    z=[]
    sum=0
    total_sum_num=0.0
    total_sum=0
    list=('H','M','L','N')
    # SQLiteデータベースに接続
    conn = sqlite3.connect('QC_DB.db')
    cursor = conn.cursor()
    # テーブルからデータを取得
    cursor.execute('SELECT category_id, second_name,third_name,importance category_name FROM subcategories')
    data = cursor.fetchall()
    # データベースの接続を閉じる
    cursor.close()
    conn.close()
    for i in list:
        for num in data:
            if num[3] ==i:
                if str(category_num)==str(num[0]) and SQuaRE_name==num[1]:
                        name_in +=[num[2]]
                        y+=[i]
                        #print(y)
                        root_node = node_calculation.make_tree(new_file, e_seet4, e_seet5, num[2])
                        z += [node_calculation.calculate_achievement(root_node)]
    for i in range(5):
        total_sum = total_sum+chenge(y[i]) 
        #print(total_sum)
    aims = [f'{chenge(y[i])/total_sum*100}' for i in range(5)]
    for i in range(5):
        total_sum_num = total_sum_num + z[i]   
    #print(total_sum_num)
    if total_sum_num!=0.0:
        aims_num = [f'{z[i]/total_sum_num*100}' for i in range(5)]
        #print(aims_num)
    else:
        aims_num=[0.0, 0.0, 0.0, 0.0, 0.0]
    for x in range(5):
        datas+=[
            go.Bar(
                x=['目標', '達成度'],
                y=[aims[x],aims_num[x]],
                name=name_in[x]
                ),
            ]
    return datas
    
#文の改行処理
def insert_line_breaks(text):
    delimiters = ['[', '○', '×', '・','①','②']
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

#貢献度のプルダウンデータ
def select_data(x):
    data = [
        {'label': '貢献度：高', 'value': 'H'},
        {'label': '貢献度：中', 'value': 'M'},
        {'label': '貢献度：低', 'value': 'L'}, 
        {'label': '貢献度：不要', 'value': 'N'}
        ]
    return data

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
        
        #2つ目：カテゴリ入力
                dbc.Row(
                    [
                        dbc.Label('2 :カテゴリ'),
                        dcc.Dropdown(
                            id='category_dropdown',
                            options=dropdown_category(),
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
                
        #3つ目：品質主特性選択   
        dbc.Row(
            [
                dbc.Label('3 :品質主特性'),
                dcc.Dropdown(
                    id='quality_dropdown',
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

        #ここから：左は自由
        dbc.Row(
                id='left_side'
            ),
        ]
    )

#右側
content = html.Div(
    [
        #タイトル
        dbc.Row(
            [
                html.H5('Quality condition model',
                        style={'margin-top': '10px'}),
            ],
            style={"height": "4vh"},
            className='bg-secondary text-white font-italic',
        ),
        
        #ここから：右は自由
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label('<品質状態モデル>'),
                        dbc.Row(id='model'),
                        dbc.Label('__表示__(貢献度 名称)'),
                        html.Br(),
                        dbc.Label('ミドリ：品質の実現'),
                        html.Br(),
                        dbc.Label('オレンジ：品質の活動'),
                    ],
                    id='right_model',
                    width=4,
                ),
                dbc.Col(
                    id='right_free',
                    width=8,
                )
            ],
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
  
#以下コールバック

# コールバック1 1 :プロジェクト名⇒2:カテゴリの制限
@app.callback(
    Output('category_dropdown', 'disabled'),
    Input('project_name', 'value')
)
def disable_input_1(input1_value):
    return not input1_value

# コールバック2 2:カテゴリ⇒3:品質主特性
@app.callback(
    Output('quality_dropdown', 'disabled'),
    Input('category_dropdown', 'value')
)
def disable_input_2(input1_value):
    return not input1_value

# コールバック3 3:品質主特性⇒左と右のレイアウト表示
@app.callback(
    Output('left_side', 'children'),
    Output('right_free','children'),
    Input('quality_dropdown', 'value'),
    State('project_name', 'value'),
    State('category_dropdown','value')
)
def disable_input_3(input1_value,priject_name,category_name):
    if input1_value is None or input1_value == '':
        return dash.no_update,dash.no_update
        
    elif input1_value=='4.2.7':
        left=[]
        right=[]
        #左
        left=[
            #4:品質副特性
            dbc.Row(
                [
                    dbc.Label('4 :品質副特性'),
                    html.Div(
                        dcc.RadioItems(
                            options=dropdown_sub(category_name,'保守性'), 
                            id='sub_SQuaRE',
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
                        id='request_dropdown',
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
                    dcc.Graph(
                        id='stacked-bar-chart',
                        figure={
                            'data': make_data(category_name,'保守性',priject_name),
                            'layout': go.Layout(
                                barmode='stack',  # 積み上げ設定
                                yaxis={'title': '割合（%）'},
                                bargroupgap=0.1,  # グループ間の間隔
                                margin={'l': 35, 'r': 20, 't': 10, 'b': 20}
                                )
                            },
                        style={'width': '100%', 'height': '330px'}
                        )

                    ],
                ),
            ]
        #右
        right=[
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
                                    style={"height": "100%",'border': '3px solid #00FF00'},
                                    )
                                ]
                            ),
        
                    dbc.Tab(
                        label='品質の評価',
                        tab_id='tab-2',
                        active_label_style={'color': 'red'},
                        children=[
                            dbc.Label('品質の評価方法'),
                            dbc.Row(
                                [
                                    html.Div(id='re_tab'),
                                    ], 
                                style={"height": "100%",'border': '3px solid #fed9a6'},
                                )
                            ]
                        ),
                    ],
                id="tabs",
                active_tab="",
                ),
            ]
        return left,right

#コールバックを作成_4 :品質副特性⇒5 :要求文
@app.callback(
    Output('request_dropdown', 'options'),
    Input('sub_SQuaRE', 'value'),
)
def up_drop(input_value): 
    options = []
    df = pd.read_excel(e_base, sheet_name=[e_seet5])
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
    return new_options

#コールバックを作成_タブの作成
@app.callback(
    Output('ar_tab', 'children'),
    Output('re_tab', 'children'),
    Input('request_dropdown', 'value'),
    State('sub_SQuaRE', 'value'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def up_data_tub(request,sub_SQueRE,name):
    #print(sub_SQueRE)
    new_file=name+'_'+e_base
    df_request = pd.read_excel(new_file, sheet_name=[e_seet5])
    df_architecture = pd.read_excel(new_file, sheet_name=[e_seet4])
    ar_tabs = []
    re_tabs = []
    if request !='その他':
        for row in df_request[e_seet5].values:
            if row[2] == request: 
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
                                                    width=2,
                                                    align="center",  
                                                    ),
                                                dbc.Col(
                                                    [
                                                    html.P(
                                                            insert_line_breaks(row[4]),
                                                            id='re_exa',
                                                            ), 
                                                    
                                                        ],
                                                    width=10,
                                                
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
                                                    width=2,
                                                    align="center",  
                                                    ),
                                                dbc.Col(
                                                    [
                                                        html.P(
                                                                insert_line_breaks(row[5]),
                                                                id='re_ex',
                                                                ), 
                                                        ],
                                                    width=5,
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
                                                    width=2,
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
                                                    width=5
                                                    ),
                                                html.Hr(),
                                            ],
                                        ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label(
                                                    '<貢献度入力>',
                                                    style={'fontSize': 15, 'fontWeight': 'bold'},
                                                    ),      
                                                ],
                                            className="text-center",
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                                dcc.Dropdown(
                                                    options=select_data(1),
                                                    id={'type': 'dropdown','index': row[3]},
                                                    placeholder='貢献度...',
                                                    value=row[8],
                                                    ),  
                                                ],
                                            width=7,
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
                if row[7] !=sub_SQueRE:
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(i[1]),
                                                    id='ar_base',
                                                    ), 
                                                
                                                ],
                                            width=10,
                                            
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(i[2]),
                                                    id='ar_in',
                                                    ), 
                                                
                                                ],
                                            width=10,
                                            
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(i[4]),
                                                    id='ar_exa',
                                                    ), 
                                                
                                                ],
                                            width=10,
                                            
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(i[5]),
                                                    id='ar_tec',
                                                    ), 
                                                
                                                ],
                                            width=10,
                                            
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(i[6]),
                                                    id='ar_tec',
                                                    ), 
                                                
                                                ],
                                            width=10,
                                            
                                            ),
                                        html.Hr(),
                                        ],
                                    ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label(
                                                    '<貢献度入力>',
                                                    style={'fontSize': 15, 'fontWeight': 'bold'},
                                                    ),      
                                                ],
                                            className="text-center",
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                                dcc.Dropdown(
                                                    options=select_data(1),
                                                    id={'type': 'dropdown','index': i[3]},
                                                    placeholder='貢献度...',
                                                    value=i[9],
                                                    ),  
                                                ],
                                            width=8,
                                            ),
                                        dbc.Col(
                                            [
                                                html.Button(
                                                    '更新',
                                                    id={'type': 'button','index': i[3]},
                                                    style={'background-color':'red',
                                                        }
                                                    ),
                                                dbc.Input(
                                                            id={'type': 'input','index': i[3]},
                                                            type='number',
                                                            value=0,
                                                            min=0,  
                                                            max=1,  
                                                            step=0.01,
                                                            valid=False,
                                                            className='mb-3',
                                                            style={'display':'none'}
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
            if row[1]==sub_SQueRE:
                re_list+=[row[7]]
                re_list+=[sub_SQueRE]
        for row in df_architecture[e_seet4].values:
            if row[7]==sub_SQueRE:
                ar_list+=[row[3]]
                ar_list+=[sub_SQueRE]
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(x[1]),
                                                    id='ar_base',
                                                    ), 
                                            
                                                ],
                                            width=10,
                                        
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(x[2]),
                                                    id='ar_in',
                                                    ), 
                                            
                                                ],
                                            width=10,
                                        
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(x[4]),
                                                    id='ar_exa',
                                                    ), 
                                            
                                                ],
                                            width=10,
                                        
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(x[5]),
                                                    id='ar_tec',
                                                    ), 
                                            
                                                ],
                                            width=10,
                                        
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
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                            html.P(
                                                    insert_line_breaks(x[6]),
                                                    id='ar_tec',
                                                    ), 
                                            
                                                ],
                                            width=10,
                                        
                                            ),
                                        html.Hr(),
                                        ],
                                    ),
                                dbc.Row(
                                    [
                                        dbc.Col(
                                            [
                                                dbc.Label(
                                                    '<貢献度入力>',
                                                    style={'fontSize': 15, 'fontWeight': 'bold'},
                                                    ),      
                                                ],
                                            className="text-center",
                                            width=2,
                                            align="center",  
                                            ),
                                        dbc.Col(
                                            [
                                                dcc.Dropdown(
                                                    options=select_data(1),
                                                    id={'type': 'dropdown','index': x[3]},
                                                    placeholder='貢献度...',
                                                    value=x[9],
                                                    ),  
                                                ],
                                            width=8,
                                            ),
                                        dbc.Col(
                                            [
                                                html.Button(
                                                    '更新',
                                                    id={'type': 'button','index': x[3]},
                                                    style={'background-color':'red',
                                                        }
                                                    ),
                                                dbc.Input(
                                                            id={'type': 'input','index': x[3]},
                                                            type='number',
                                                            value=0,
                                                            min=0,  
                                                            max=1,  
                                                            step=0.01,
                                                            valid=False,
                                                            className='mb-3',
                                                            style={'display':'none'}
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
    Output('re_tabs', 'active_tab'),
    Output('stacked-bar-chart','figure'),
    Output('model','children'),
    Input({'type': 'button', 'index': ALL}, 'n_clicks'),
    State({'type': 'dropdown','index': ALL},'value'),
    State({'type': 'dropdown','index': ALL},'id'),
    State({'type': 'input','index': ALL},'value'),
    State('project_name', 'value'),
    State('category_dropdown','value'),
    prevent_initial_call=True
)
def update_output(n_clicks_list,values,id,values1,name,category_name):
    if not n_clicks_list or all(n is None for n in n_clicks_list):
        raise dash.exceptions.PreventUpdate
    ctx = dash.callback_context
    triggered_id = ctx.triggered_id
    children=[]
    if triggered_id is not None:
        button_id = triggered_id['index']
        index_values = [item['index'] for item in id]
        df_ar = pd.read_excel(name+'_'+e_base, sheet_name=[e_seet4])
        df_re = pd.read_excel(name+'_'+e_base, sheet_name=[e_seet5])
        for row in df_ar[e_seet4].values:
            if row[3]==button_id:
                id=row[8]
                for a,b in zip(index_values,values):
                    if a==button_id:
                        for row in df_ar[e_seet4].values:
                            if row[3]==button_id:
                                write_file_ar(name+'_'+e_base,button_id,b)
        for row in df_re[e_seet5].values:
            if row[3]==button_id:
                id=row[1]
                for a,b in zip(index_values,values):
                    if a==button_id:
                        for c,d in zip(index_values,values1):
                            if c==button_id:                
                                for row in df_re[e_seet5].values:
                                    if row[3]==button_id:
                                        write_file_re(name+'_'+e_base,button_id,b,d)
        data=make_data(category_name,'保守性',name)
        figure={
            'data': data,
            'layout': go.Layout(
                barmode='stack',  # 積み上げ設定
                yaxis={'title': '割合（%）'},
                bargroupgap=0.1,  # グループ間の間隔
                margin={'l': 35, 'r': 20, 't': 10, 'b': 20}
                )
            }
        root_node = node_calculation.make_tree(name+'_'+e_base, e_seet4, e_seet5, id) 
        
        children=[node_calculation.tree_display(root_node,name)]
        #print(children)
        return '','',figure,children

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
        

if __name__ == "__main__":
    app.run_server(debug=True)