import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State, ALL
import sqlite3
from .core import write_DB, node_calculation
import pandas as pd
import plotly.graph_objs as go
import re

data = (13, 59, 1, 'planning  ', '試験', '1')

### 保守性_DB.exslのシート名###
e_base = '保守性_DB.xlsx'
e_seet1 = 'SQuaRE'
e_seet2 = 'maintainability'
e_seet3 = 'architecture'
e_seet4 = 'request'

# 貢献度を数字に変換


def chenge_int(x):
    if x == 'H':
        return int(3)
    elif x == 'M':
        return int(2)
    elif x == 'L':
        return int(1)
    else:
        return int(0)

# 貢献度を検索


def search(category_num, node):
    conn = sqlite3.connect('QC_DB.db')
    cursor = conn.cursor()
    # テーブルからデータを取得
    cursor.execute(
        'SELECT importance FROM subcategories WHERE category_id = ? AND third_name = ?', (category_num, node))
    data = cursor.fetchall()
    # データベースの接続を閉じる
    cursor.close()
    conn.close()
    re_data = data[0]
    return chenge_int(re_data[0])


# 貢献度％計算
tree_contribution = []
tree_name = []


def calculate_contribution_percentage(node, x=None):
    global tree_contribution, tree_name
    if node is None:
        return None
    elif type(node) != str:
        if x == None:
            tree_name = []
            tree_contribution = []
        if node.children is not None:
            total_contribution = 0
            child_contribution = []
            child_name = []
            # 子ノードの貢献度の合計を計算
            for child in node.children:
                total_contribution += child.contribution
                child_name += [child.id]
                child_contribution += [child.contribution]
            # この名前と合計を記録
            for x, y in zip(child_name, child_contribution):
                tree_name += [x]
                tree_contribution += [round(y/total_contribution*100)]
            for child in node.children:
                calculate_contribution_percentage(child, x=1)
        return 0

    else:
        # print(tree_contribution)
        # print(tree_name)
        for x, y in zip(tree_name, tree_contribution):
            if x == node:
                return y


# グラフ作成
def make_data(mae, now):
    labels = ['達成', '未達成']
    previous = [now, 100 - now]
    current = [mae, 100 - mae]
    colors = ['#FF9999', 'rgb(255, 0, 0)']

    trace_previous = go.Pie(
        labels=labels,
        values=previous,
        sort=False,
        hole=0,
        textinfo='none',  # ラベルを非表示
        hoverinfo='none',
        marker=dict(colors=[colors[1], 'rgba(0,0,0,0)'],
                    line=dict(color='black', width=1))
    )
    trace_current = go.Pie(
        labels=labels,
        values=current,
        hole=0,
        sort=False,
        textinfo='none',  # ラベルを非表示
        hoverinfo='none',
        marker=dict(colors=[colors[0], 'rgba(0,0,0,0)'],
                    line=dict(color='black', width=1))
    )

    figure = go.Figure(data=[trace_previous, trace_current])
    figure.update_layout(
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(
            size=9
        ),
        autosize=False,
        height=37,
        width=37,
        margin=dict(l=1, r=1, t=1, b=1),
    )
    return figure

# プルダウンのカテゴリ


def dropdown_sub(category_num, SQuaRE_name):
    options = []
    list = ('H', 'M', 'L', 'N')
    color_list = ('red', 'orange', 'LightGreen', 'MediumTurqoise')
    # SQLiteデータベースに接続
    conn = sqlite3.connect('QC_DB.db')
    cursor = conn.cursor()
    # テーブルからデータを取得
    cursor.execute(
        'SELECT category_id, second_name,third_name,importance category_name FROM subcategories')
    data = cursor.fetchall()
    # データベースの接続を閉じる
    cursor.close()
    conn.close()
    x = 0
    for i in list:
        for num in data:
            if num[3] == i:
                if str(category_num) == str(num[0]) and SQuaRE_name == num[1]:
                    options += {
                        'label': html.Div(num[2], style={'color': color_list[x], 'font-size': 15}),
                        'value': num[2],
                    },
        x = x+1
    return options

# 要求文の作成


def make_request(node, node_data):
    df = pd.read_excel(e_base, sheet_name=[e_seet4])
    options = []
    for row in df[e_seet4].values:
        if row[1] == node:
            options += [
                {
                    'label': row[2],
                    'value': row[2],
                }
            ]
        count = 0
        new_options = []
        for x in options:
            for y in new_options:
                if x == y:
                    count = count+1
            if count == 0:
                new_options += [x]
            count = 0
    if node_data.children is not None:
        for children in node_data.children:
            for row in df[e_seet4].values:
                if row[3] == children.id or row[7] == children.id:
                    for option in new_options:
                        label = option['label']
                        if label == row[2]:
                            option['disabled'] = True
    return new_options

# 各名称の作成


def make_adovaic_node(node):
    df_request = pd.read_excel(e_base, sheet_name=[e_seet4])
    df_architecture = pd.read_excel(e_base, sheet_name=[e_seet3])
    options = []
    for row in df_request[e_seet4].values:
        if row[2] == node:
            options += [
                {
                    'label': html.Div('<品質実現>', style={'font-size': 15}),
                    'value': 0,
                    'disabled': True
                }
            ]
            for ri in df_architecture[e_seet3].values:
                if ri[3] == row[7]:
                    options += [
                        {
                            'label': html.Div(ri[3], style={'font-size': 15}),
                            'value': ri[3],
                        }
                    ]
            options += [
                {
                    'label': html.Div('<品質活動>', style={'font-size': 15}),
                    'value': 0,
                    'disabled': True
                }
            ]
            options += [
                {
                    'label': html.Div(row[3], style={'font-size': 15}),
                    'value': row[3],
                }
            ]
    return options

# 各名称の作成_子供あり


def make_adovaic_node_children(node, node_data):
    df_request = pd.read_excel(e_base, sheet_name=[e_seet4])
    df_architecture = pd.read_excel(e_base, sheet_name=[e_seet3])
    options = []
    for row in df_request[e_seet4].values:
        if row[3] == node or row[7] == node:
            options += [
                {
                    'label': html.Div('<品質実現>', style={'font-size': 15}),
                    'value': 0,
                    'disabled': True
                }
            ]
            for ri in df_architecture[e_seet3].values:
                if ri[3] == row[7]:
                    options += [
                        {
                            'label': html.Div(ri[3], style={'font-size': 15}),
                            'value': ri[3],
                        }
                    ]
            options += [
                {
                    'label': html.Div('<品質活動>', style={'font-size': 15}),
                    'value': 0,
                    'disabled': True
                }
            ]
            options += [
                {
                    'label': html.Div(row[3], style={'font-size': 15}),
                    'value': row[3],
                }
            ]
    for option in options:
        value = option['value']
        if value == node:
            option['disabled'] = True
    if node_data.children is not None:
        for option in options:
            value = option['value']
            for children in node_data.children:
                if value == children.id:
                    option['disabled'] = True
    return options

# 文の改行処理


def insert_line_breaks(text):
    delimiters = ['[', '○', '×', '・', '①', '②']
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

# 貢献度のプルダウンデータ


def select_data():
    data = [
        {'label': '貢献度：高', 'value': '3'},
        {'label': '貢献度：中', 'value': '2'},
        {'label': '貢献度：低', 'value': '1'},
        {'label': '貢献度：不要', 'value': '0'}
    ]
    return data

# ツリー表示用の関数


def tree_display(node, indent=''):
    print(node.id,node.type)
    df = pd.read_excel(e_base, sheet_name=[e_seet4])
    if node is None:
        return None
    else:
        if node.type == 'REQ':
            before = write_DB.check_achievement_old(data[1], node.id)
            now = write_DB.check_achievement(data[1], node.id)
            com = '達成:'+str(now)+'%'
            if node.id == '保守性':
                tree = html.Details(
                    [
                        html.Summary(
                            [
                                html.P('[' + str(calculate_contribution_percentage(node)) + '%' + ']', style={
                                       'display': 'none', 'fontSize': 12, 'marginRight': '10px'}),
                                html.P('品質要求', style={
                                       'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                                dbc.Popover(
                                    dbc.RadioItems(
                                        options=dropdown_sub(data[5], node.id),
                                        id={'type': 'radio', 'index': node.id},
                                    ),
                                    # id={'type': 'popover','index': node.id},
                                    target={'type': 'button',
                                            'index': node.id},
                                    body=True,
                                    trigger="hover",
                                ),
                                html.P(com, style={
                                       'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                html.P(
                                    dcc.Graph(
                                        figure=make_data(before, now),
                                        config={
                                            'displayModeBar': False
                                        },
                                    ),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                ),
                            ],
                        ),
                    ],
                    open=True,
                )
            else:
                tree = html.Details(
                    [
                        html.Summary(
                            [
                                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                       'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                html.P('品質要求', style={
                                       'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                                dbc.Popover(
                                    dbc.RadioItems(
                                        options=make_request(node.id, node),
                                        id={'type': 'radio', 'index': node.id},
                                    ),
                                    target={'type': 'button',
                                            'index': node.id},
                                    body=True,
                                    trigger="hover",
                                ),
                                html.P(com, style={
                                       'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                html.P(
                                    dcc.Graph(
                                        figure=make_data(before, now),
                                        config={
                                            'displayModeBar': False
                                        },
                                    ),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                ),
                            ],
                        ),
                    ],
                    open=True,
                    style={'margin-left': '15px'},
                )
        elif node.type == 'IMP':
            if node.parent and node.parent.type == 'REQ' and node.type != 'REQ':
                ver = 0
                for row in df[e_seet4].values:
                    if row[7] == node.id:
                        ver = 1
                        break
                    elif row[3] == node.id+'率':
                        ver = 3
                        break
                    else:
                        ver = 2
                print(node.id, ver)
                if ver == 1 :
                    text = ''
                    for row in df[e_seet4].values:
                        if row[7] == node.id:
                            text = row[2]
                            break
                    before = write_DB.check_achievement_old(data[1], node.id)
                    now = write_DB.check_achievement(data[1], node.id)
                    com = '達成:'+str(now)+'%'
                    tree = html.Details(
                        [
                            html.Summary(
                                [
                                    html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                        'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                    html.P('PQ要求文：', style={
                                        'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                                    html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={
                                                'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline', }),
                                    dbc.Popover(
                                        dbc.RadioItems(
                                            options=make_adovaic_node_children(
                                                node.id, node),
                                            id={'type': 'radio',
                                                'index': node.id},
                                        ),
                                        id='popover',
                                        target={'type': 'button',
                                                'index': 'ex'+node.id},
                                        body=True,
                                        trigger="hover",
                                    ),
                                    html.P(com, style={
                                        'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                    html.P(
                                        dcc.Graph(
                                            figure=make_data(before, now),
                                            config={
                                                'displayModeBar': False
                                            },
                                        ),
                                        style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                               'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                    ),

                                ],
                            ),
                        ],
                        open=True,
                        style={'margin-left': '15px'}
                    )
                    before = write_DB.check_achievement_old(data[1], node.id)
                    now = write_DB.check_achievement(data[1], node.id)
                    com = '達成:'+str(now)+'%'
                    tree.children.append(html.Details(
                        [
                            html.Summary(
                                [
                                    html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                        'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                    html.P('品質実現', style={
                                        'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                    html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                                'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                                    html.P(com, style={
                                        'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                    html.P(
                                        dcc.Graph(
                                            figure=make_data(before, now),
                                            config={
                                                'displayModeBar': False
                                            },
                                        ),
                                        style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                               'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                    ),
                                ],
                            ),
                            html.P('実現手法：' + str(node.other),
                                   style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                        ],
                        style={'margin-left': '15px', 'marginBottom': '5px'}
                    )
                    )
                elif ver == 2:
                    before = write_DB.check_achievement_old(data[1], node.id)
                    now = write_DB.check_achievement(data[1], node.id)
                    com = '達成:'+str(now)+'%'
                    tree = html.Details(
                        [
                            html.Summary(
                                [
                                    html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                         'display': 'inline-block','fontSize': 12, 'marginRight': '10px'}),
                                    html.P('品質実現', style={
                                        'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                    html.Button(node.id, style={
                                                'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none',  'border': 'none'}),
                                    
                                    html.P(com, style={
                                        'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                    html.P(
                                        dcc.Graph(
                                            figure=make_data(before, now),
                                            config={
                                                'displayModeBar': False
                                            },
                                        ),
                                        style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                            'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                    ),
                                ],
                            ),
                        ],
                        style={'margin-left': '15px'},
                    )

                else:
                    text = ''
                    for row in df[e_seet4].values:
                        if row[3] == node.id+'率':
                            text = row[2]
                            child=row[9]
                            break
                    before = write_DB.check_achievement_old(data[1], node.id)
                    now = write_DB.check_achievement(data[1], node.id)
                    com = '達成:'+str(now)+'%'
                    tree = html.Details(
                        [
                            html.Summary(
                                [
                                    html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                        'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                    html.P('PQ要求文：', style={
                                        'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                                    html.Button(text, style={
                                                'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline', }),
                                    html.P(com, style={
                                        'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                    html.P(
                                        dcc.Graph(
                                            figure=make_data(before, now),
                                            config={
                                                'displayModeBar': False
                                            },
                                        ),
                                        style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                               'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                    ),

                                ],
                            ),
                        ],
                        open=True,
                        style={'margin-left': '15px'}
                    )
                    result = child.split(',')
                    tree_node=[]
                    for row in df[e_seet4].values:
                        for x in result:
                            if row[7] == x:
                                before = write_DB.check_achievement_old(data[1], x)
                                now = write_DB.check_achievement(data[1], x)
                                com = '達成:'+str(now)+'%'
                                other = write_DB.check_description(data[1],x)
                                child_before = write_DB.check_achievement_old(data[1], row[3])
                                child_now = write_DB.check_achievement(data[1], row[3])
                                child_com = '達成:'+str(child_now)+'%'
                                child_other = write_DB.check_scope(data[1],row[3])
                                tree_node.append(
                                    html.Details(
                                        [
                                            html.Summary(
                                                [
                                                    html.P('[50%]', style={
                                                        'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                                    html.P('PQ要求文：', style={
                                                        'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                                                    html.Button(row[2], style={
                                                                'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline', }),
                                                    html.P(com, style={
                                                        'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                                    html.P(
                                                        dcc.Graph(
                                                            figure=make_data(before, now),
                                                            config={
                                                                'displayModeBar': False
                                                            },
                                                        ),
                                                        style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                            'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                                    ),
                                                ],
                                            ),
                                            html.Details(
                                                [ 
                                                    html.Summary(
                                                        [
                                                            html.P('[50%]', style={
                                                                'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                                            html.P('品質実現', style={
                                                                'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                                            html.Button(x, style={
                                                                'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'border': 'none'}),
                                                            html.P(com, style={
                                                                'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                                            html.P(
                                                                dcc.Graph(
                                                                    figure=make_data(before, now),
                                                                    config={
                                                                        'displayModeBar': False
                                                                    },
                                                                ),
                                                                style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                                    'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                                                ),
                                                            ],
                                                        ),
                                                    html.P('実現手法：' + str(other),
                                                    style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
                                                ],
                                                style={'margin-left': '15px',
                                                        'marginBottom': '5px'},
                                            ),
                                            html.Details(
                                                [ 
                                                    html.Summary(
                                                        [
                                                            html.P('[100%]', style={
                                                                'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                                            html.P('品質活動', style={
                                                                'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                                            html.Button(row[3], style={
                                                                'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'border': 'none'}),
                                                            html.P(child_com, style={
                                                                'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                                            html.P(
                                                                dcc.Graph(
                                                                    figure=make_data(child_before, child_now),
                                                                    config={
                                                                        'displayModeBar': False
                                                                    },
                                                                ),
                                                                style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                                    'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                                                ),
                                                            ],
                                                        ),
                                                    html.P('許容範囲：' + str(child_other),
                                                    style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
                                                ],
                                                style={'margin-left': '30px',
                                                        'marginBottom': '5px'},
                                            ) 
                                        ],
                                        style={'margin-left': '30px'}
                                    )
                                )                               
                        
                    before = write_DB.check_achievement_old(data[1], node.id)
                    now = write_DB.check_achievement(data[1], node.id)
                    com = '達成:'+str(now)+'%'
                    tree.children.append(
                        html.Details(
                            [
                                html.Summary(
                                    [
                                        html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                            'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                        html.P('品質実現', style={
                                            'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                        html.Button(node.id, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'border': 'none'}),
                                        html.P(com, style={
                                            'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                        html.P(
                                            dcc.Graph(
                                                figure=make_data(before, now),
                                                config={
                                                    'displayModeBar': False
                                                },
                                            ),
                                            style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                   'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                        ),
                                    ],
                                ),

                                html.Div(tree_node),
                                   
                            ],
                            style={'margin-left': '15px',
                                   'marginBottom': '5px'}
                        )
                    )
            else:
                text = ''
                for row in df[e_seet4].values:
                    if row[7] == node.id:
                        text = row[2]
                        break
                before = write_DB.check_achievement_old(data[1], node.id)
                now = write_DB.check_achievement(data[1], node.id)
                com = '達成:'+str(now)+'%'
                tree = html.Details(
                    [
                        html.Summary(
                            [
                                html.P('[+]', style={
                                    'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                html.P('PQ要求文：', style={
                                    'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={
                                            'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline', }),
                                dbc.Popover(
                                    dbc.RadioItems(
                                        options=make_adovaic_node_children(
                                            node.id, node),
                                        id={'type': 'radio',
                                            'index': node.id},
                                    ),
                                    id='popover',
                                    target={'type': 'button',
                                            'index': 'ex'+node.id},
                                    body=True,
                                    trigger="hover",
                                ),
                                html.P(com, style={
                                    'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                html.P(
                                    dcc.Graph(
                                        figure=make_data(before, now),
                                        config={
                                            'displayModeBar': False
                                        },
                                    ),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                            'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                ),

                            ],
                        ),
                    ],
                    open=True,
                    style={'margin-left': '15px'}
                )
                before = write_DB.check_achievement_old(data[1], node.id)
                now = write_DB.check_achievement(data[1], node.id)
                com = '達成:'+str(now)+'%'
                tree.children.append(html.Details(
                    [
                        html.Summary(
                            [
                                html.P('[+]', style={
                                    'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                html.P('品質実現', style={
                                    'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                                html.P(com, style={
                                    'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                html.P(
                                    dcc.Graph(
                                        figure=make_data(before, now),
                                        config={
                                            'displayModeBar': False
                                        },
                                    ),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                            'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                ),
                            ],
                        ),
                        html.P('実現手法：' + str(node.other),
                                style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
                        #html.P('加算割合：' + str(node.other),
                        #        style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                    ],
                    style={'margin-left': '15px', 'marginBottom': '5px'}
                )
                )
        elif node.type == 'ACT':
            if node.parent and node.parent.type == 'REQ' and node.type != 'REQ':
                text = ''
                for row in df[e_seet4].values:
                    if row[3] == node.id:
                        text = row[2]
                        break
                before = write_DB.check_achievement_old(data[1], node.id)
                now = write_DB.check_achievement(data[1], node.id)
                com = '達成:'+str(now)+'%'
                tree = html.Details(
                    [
                        html.Summary(
                            [
                                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                    'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                html.P('PQ要求文：', style={
                                    'display': 'inline-block', 'marginRight': '10px', 'fontSize': 10}),
                                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline', }),
                                dbc.Popover(
                                    dbc.RadioItems(
                                        options=make_adovaic_node_children(
                                            node.id, node),
                                        id={'type': 'radio', 'index': node.id},
                                    ),
                                    id='popover',
                                    target={'type': 'button',
                                            'index': 'ex'+node.id},
                                    body=True,
                                    trigger="hover",
                                ),
                                html.P(com, style={
                                    'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                html.P(
                                    dcc.Graph(
                                        figure=make_data(before, now),
                                        config={
                                            'displayModeBar': False
                                        },
                                    ),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                ),
                            ],
                        ),
                    ],
                    open=True,
                    style={'margin-left': '15px'}
                )
                before = write_DB.check_achievement_old(data[1], node.id)
                now = write_DB.check_achievement(data[1], node.id)
                com = '達成:'+str(now)+'%'
                tree.children.append(html.Details(
                    [
                        html.Summary(
                            [
                                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                       'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                                html.P('品質活動', style={
                                       'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                                html.P(com, style={
                                       'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                html.P(
                                    dcc.Graph(
                                        figure=make_data(before, now),
                                        config={
                                            'displayModeBar': False
                                        },
                                    ),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                ),
                            ],
                        ),
                        html.P('許容範囲：' + str(node.other),
                               style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                    ],

                    style={'margin-left': '15px'}
                )
                )
            else:
                before = write_DB.check_achievement_old(data[1], node.id)
                now = write_DB.check_achievement(data[1], node.id)
                com = '達成:'+str(now)+'%'
                tree = html.Details(
                    [
                        html.Summary(
                            [
                                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                                       'display': 'inline-block', 'fontSize': 12, 'marginRight': '2px', 'marginRight': '10px'}),
                                html.P('品質活動', style={
                                       'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                                html.P(com, style={
                                       'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                                html.P(
                                    dcc.Graph(
                                        figure=make_data(before, now),
                                        config={
                                            'displayModeBar': False
                                        },
                                    ),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                                ),
                            ],
                        ),
                        html.P('許容範囲：' + str(node.other),
                               style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                    ],
                    style={'margin-left': '30px'},
                )
        elif node.type == 'QRM':
            # before = 40
            # now = 45
            # com = '達成:'+str(now)+'%'
            tree = html.Details(
                [
                    html.Summary(
                        [
                            # html.P('['+ str(int(calculate_contribution_percentage(node)))+ '%' + ']', style={'display': 'inline-block', 'fontSize': 12,'marginRight': '10px'}),
                            html.P('PQ要求文：', style={
                                'display': 'inline-block', 'marginRight': '10px', 'fontSize': 10}),
                            html.Span(node.id, id={'type': 'button', 'index': node.id}, style={
                                      'display': 'inline-block', 'marginRight': '15px', 'textDecoration': 'underline', 'fontSize': 12}),
                            dbc.Popover(
                                dbc.RadioItems(
                                    options=make_adovaic_node(node.id),
                                    id={'type': 'radio', 'index': node.id},
                                ),
                                id='popover',
                                target={'type': 'button',
                                        'index': node.id},
                                body=True,
                                trigger="hover",
                            ),

                        ],
                    ),
                ],
                open=True,
                style={'margin-left': '15px'}
            )
        if node.children:
            children = [tree_display(child, indent + "　")
                        for child in node.children]
            tree.children.append(html.Div(children))
    return tree


### 左側###
sidebar = html.Div(
    [
        # project情報
        dbc.Row(
            [
                html.H5('project', style={'flex-direction': 'column', 'backgroundColor': '#2d3748',
                        'color': 'white', 'text-align': 'center', "height": "4vh"}),
                html.P('project:', style={
                       'display': 'inline-block', 'width': '70px'}),
                html.P(data[4], style={
                       'display': 'inline-block', 'width': '200px'}),
                html.P('sprint:', style={
                       'display': 'inline-block', 'width': '70px'}),
                html.P(data[2], style={
                       'display': 'inline-block', 'width': '30px'}),
                html.P(data[3], style={
                       'display': 'inline-block', 'width': '100px'}),
            ],
        ),

        dbc.Row(
            [
                html.H5('setting', style={'flex-direction': 'column', 'backgroundColor': '#2d3748',
                                          'color': 'white', 'text-align': 'center', "height": "4vh"}),
            ],
        ),
        dbc.Row(
            [
                dcc.RadioItems(
                    options=[
                        {'label': '有効性', 'value': '有効性', 'disabled': True},
                        {'label': '効率性', 'value': '効率性', 'disabled': True},
                        {'label': '満足性', 'value': '満足性', 'disabled': True},
                        {'label': 'リスク回避性', 'value': 'リスク回避性', 'disabled': True},
                        {'label': '利用状況網羅性', 'value': '利用状況網羅性', 'disabled': True},
                        {'label': '保守性', 'value': '保守性'},
                        {'label': '移植性', 'value': '移植性', 'disabled': True},

                    ],
                    id='select',
                    labelStyle={
                        "display": "flex",
                        "align-items": "center",
                        'width': '100%',
                        'background-color': 'white',
                        'marginRight': '20px'
                    },
                ),
                dbc.Modal(
                    [
                        dbc.ModalHeader(
                            dbc.ModalTitle('attention'), close_button=False
                        ),
                        dbc.ModalBody(
                            '[PQ要求：複数のクラスで定義できるようにする]：４割　と[PQ要求：実行時に柔軟性を持たせる]：６割　でセットで評価するので，必ずどちらの要求も品質実現，品質活動を入力てください'
                        ),
                        dbc.ModalFooter(dbc.Button(
                            "Close", id="close-dismiss")),
                    ],
                    id="modal-dismiss",
                    keyboard=False,
                    backdrop="static",
                ),
            ],
            style={'margin': '0', 'background-color': 'white'}
        ),
    ],
),

### モデル###
model = html.Div(
    [
        dbc.Row(
            [
                html.H5('model', style={'flex-direction': 'column', 'backgroundColor': 'black',
                                        'color': 'white', 'text-align': 'center', "height": "4vh"}),
            ],
        ),
        # モデル自由
        dbc.Row(
            id='model_free',
            style={'overflowY': 'scroll', 'height': '90vh'}
        ),
    ],
)
### 右側###
content = html.Div(
    [
        # タイトル
        dbc.Row(
            [
                html.H5('Quality condition model',
                        style={'flex-direction': 'column', 'backgroundColor': '#2d3748',
                               'color': 'white', 'text-align': 'center', "height": "4vh"}),
            ],
        ),

        # ここから：右は自由
        dbc.Row(
            id='right_free',
        ),
    ],
)


edit_layout = dbc.Container(
    [
        dbc.Row(
            [
                dbc.Col(sidebar, width=2),
                dbc.Col(model, width=3, className='bg-light'),
                dbc.Col(content, width=7)
            ],
            style={'height': '95vh'}
        ),
    ],
    fluid=True
)


@callback(
    Output('model_free', 'children'),
    Output('right_free', 'children'),
    Input('select', 'value'),
    Input({'type': 'button', 'index': ALL}, 'n_clicks'),
    Input({'type': 'radio', 'index': ALL}, 'value'),
    State({'type': 'input', 'index': ALL}, 'value'),
    Input({'type': 'dropdown', 'index': ALL}, 'value'),
    prevent_initial_call=True
)
def up_node(input_value, button_list, radio_list, input_list, drop_list):
    if input_value is None:
        raise dash.exceptions.PreventUpdate
    else:
        print('input', input_value)
        print('button', button_list)
        print('radio', radio_list)
        print('input', input_list)
        print('drop', drop_list)
        if (button_list == []) and (radio_list == []) and (input_list == []) and (drop_list == []):
            df = pd.read_excel(e_base, sheet_name=[e_seet1])
            for row in df[e_seet1].values:
                if row[1] == input_value:
                    statement = row[2]
                    write_DB.write_node(data[1], row[1], 'REQ', 'pq', {
                                        'subchar': row[1], 'statement': statement}, 1, 0)
                    node = node_calculation.make_tree(data[4], '保守性')
                    return tree_display(node), []
        elif (input_list == []) and (drop_list == []):
            radio_num = [value for value in radio_list if value is not None]
            button_check = [
                value for value in button_list if value is not None]
            print(radio_num)
            print(button_check)
            if button_check == []:
                df_square = pd.read_excel(e_base, sheet_name=[e_seet2])
                for row in df_square[e_seet2].values:
                    if row[1] == radio_num[0]:
                        statement = row[2]
                        write_DB.write_node(data[1], row[1], 'REQ', 'pq', {'subchar': row[1], 'statement': statement}, search(
                            data[5], radio_num[0]), write_DB.check_nid(data[4], input_value))
                        node = node_calculation.make_tree(data[4], '保守性')
                        return tree_display(node), []
                df_request = pd.read_excel(e_base, sheet_name=[e_seet4])
                for row in df_request[e_seet4].values:
                    if row[2] == radio_num[0]:
                        print(row[8])
                        if row[8] == 1 or row[8] == 2:
                            node1 = node_calculation.make_tree(data[4], '保守性')
                            node = node_calculation.add_child_to_node(
                                node1, row[1], row[2], 1, 1, 'QRM')
                            return tree_display(node), []
                        else:
                            result = row[9].split(',')
                            for row in df_request[e_seet4].values:
                                for x in result:
                                    if row[7] == x:
                                        x1 = write_DB.check_nid(
                                            data[4], row[3])
                                        x2 = write_DB.check_nid(data[4], x)
                                        if x1 == 'none' or x2 == 'none':
                                            return dash.no_update, ['QP要求文：['+row[2]+']　'+'の品質実現または，品質活動が未設定のため，追加できません']
                            node1 = node_calculation.make_tree(data[4], '保守性')
                            node = node_calculation.add_child_to_node(
                                node1, row[1], radio_num[0], 1, 1, 'QRM')
                            return tree_display(node), []

                return dash.no_update, message_display(radio_num[0])
            else:
                ctx = dash.callback_context
                triggered_id = ctx.triggered_id
                button_id = triggered_id['index']
                print('hererr', button_id)
                df_arc = pd.read_excel(e_base, sheet_name=[e_seet3])
                for row in df_arc[e_seet3].values:
                    if row[3] == button_id:
                        return dash.no_update, message_display(button_id)
                df_re = pd.read_excel(e_base, sheet_name=[e_seet4])
                for row in df_re[e_seet4].values:
                    if row[3] == button_id:
                        return dash.no_update, message_display(button_id)
                node = node_calculation.make_tree(data[4], '保守性')
                return tree_display(node), dash.no_update
        else:
            radio_num = [value for value in radio_list if value is not None]
            button_check = [
                value for value in button_list if value is not None]
            if button_check == []:
                return dash.no_update, dash.no_update
            elif button_check == [1] or button_check == [2]:
                ctx = dash.callback_context
                triggered_id = ctx.triggered_id
                button_id = triggered_id['index']
                print(button_id)
                if button_id[:3] == 're_':
                    index = button_id.index("re_") + len("re_")
                    rest_of_text = button_id[index:]
                    input_num = [
                        value for value in input_list if value is not None]
                    if input_num == []:
                        input_num += ['未記入']
                    df_arc = pd.read_excel(e_base, sheet_name=[e_seet3])
                    for row1 in df_arc[e_seet3].values:
                        if row1[3] == rest_of_text:
                            df_re = pd.read_excel(e_base, sheet_name=[e_seet4])
                            for row_2 in df_re[e_seet4].values:
                                if row_2[7] == rest_of_text:
                                    child_nid = write_DB.check_nid(
                                        data[4], row_2[3])
                                    if child_nid == 'none':
                                        if row_2[8] == 2:
                                            pid=write_DB.check_nid(data[4], 'セット')
                                            if pid !='none':
                                                write_DB.write_node(data[1], row1[3], 'IMP', 'arch', {
                                                            'subchar': row1[3],'description': input_num[0]}, 1,pid,child_nid)
                                            else:
                                                write_DB.write_node(data[1], 'セット', 'IMP', 'arch', {
                                                                'subchar': 'セット','description': '以下で実現'}, drop_list[0], write_DB.check_nid(data[4], row1[7]))
                                                write_DB.write_node(data[1], row1[3], 'IMP', 'arch', {
                                                                'subchar': row1[3],'description': input_num[0]}, 1, write_DB.check_nid(data[4], 'セット'),child_nid)
                                            break
                                        else:
                                            write_DB.write_node(data[1], row1[3], 'IMP', 'arch', {
                                                            'subchar': row1[3], 'description': input_num[0]}, drop_list[0], write_DB.check_nid(data[4], row1[7]))
                                        
                                    else:
                                        if row_2[8] == 2:
                                            pid=write_DB.check_nid(data[4], 'セット')
                                            if pid !='none':
                                                write_DB.write_node(data[1], row1[3], 'IMP', 'arch', {
                                                            'subchar': row1[3],'description': input_num[0]}, 1,pid,child_nid)
                                            else:
                                                write_DB.write_node(data[1], 'セット', 'IMP', 'arch', {
                                                                'subchar': 'セット','description': '以下で実現'}, drop_list[0], write_DB.check_nid(data[4], row1[7]))
                                                write_DB.write_node(data[1], row1[3], 'IMP', 'arch', {
                                                                'subchar': row1[3],'description': input_num[0]}, 1, write_DB.check_nid(data[4], 'セット'),child_nid)
                                            break
                                        else:
                                            write_DB.write_node(data[1], row1[3], 'IMP', 'arch', {
                                                            'subchar': row1[3], 'description': input_num[0]}, drop_list[0], write_DB.check_nid(data[4], row1[7]), child_nid)
                    df_re = pd.read_excel(e_base, sheet_name=[e_seet4])
                    for row_2 in df_re[e_seet4].values:
                        if row_2[3] == rest_of_text:
                            parent_id = write_DB.check_nid(data[4], row_2[7])
                            if parent_id == 'none':
                                write_DB.write_node(data[1], row_2[3], 'ACT', 'sa', {
                                                    'subchar': row_2[3], 'tolerance': input_num[0]}, drop_list[0], write_DB.check_nid(data[4], row_2[1]))
                                break
                            else:
                                if row_2[8] == 1 or row_2[8] == 2:
                                    write_DB.write_node(data[1], row_2[3], 'ACT', 'sa', {
                                                        'subchar': row_2[3], 'tolerance': input_num[0]}, drop_list[0], parent_id)
                                else:
                                    write_DB.write_node(data[1], row_2[3][:-1], 'IMP', 'arch', {
                                                        'subchar': row_2[3][:-1], 'description': '以下を参照'}, drop_list[0], parent_id)
                                    write_DB.write_node(data[1], row_2[3], 'ACT', 'sa', {
                                                        'subchar': row_2[3], 'tolerance': input_num[0]}, drop_list[0], write_DB.check_nid(data[4], row_2[3][:-1]))

                    node = node_calculation.make_tree(data[4], '保守性')
                    node_calculation.print_tree(node)
                    return tree_display(node), []

                else:
                    df_ar = pd.read_excel(e_base, sheet_name=[e_seet3])
                    for row_1 in df_ar[e_seet3].values:
                        if row_1[3] == button_id:
                            return dash.no_update, message_display(row_1[3])
                    df_re = pd.read_excel(e_base, sheet_name=[e_seet4])
                    for row_2 in df_re[e_seet4].values:
                        if row_2[3] == button_id:
                            return dash.no_update, message_display(row_2[3])

            return dash.no_update, dash.no_update


def message_display(node):
    print('message_node', node)
    if node is None:
        return None
    else:
        children = []
        df_request = pd.read_excel(e_base, sheet_name=[e_seet4])
        df_architecture = pd.read_excel(e_base, sheet_name=[e_seet3])
        for row in df_architecture[e_seet3].values:
            if row[3] == node:
                children = [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        '<基本戦略>',
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
                                    ),
                                ],
                                className="text-center",
                                width=2,
                                align="center",
                            ),
                            dbc.Col(
                                [
                                    html.P(
                                        insert_line_breaks(row[1]),
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
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
                                    ),
                                ],
                                className="text-center",
                                width=2,
                                align="center",
                            ),
                            dbc.Col(
                                [
                                    html.P(
                                        insert_line_breaks(row[2]),
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
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
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
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
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
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
                                    ),
                                ],
                                className="text-center",
                                width=2,
                                align="center",
                            ),
                            dbc.Col(
                                [
                                    html.P(
                                        insert_line_breaks(row[6]),
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
                                        '<実現手法入力>',
                                        style={
                                            'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'},
                                    ),
                                ],
                                className="text-center",
                                width=2,
                                align="center",
                            ),
                            dbc.Col(
                                [
                                    dbc.Input(
                                        id={'type': 'input',
                                            'index': 're_'+row[3]},
                                        type='text',
                                        value=write_DB.check_description(
                                            data[1], row[3]),
                                        placeholder='手法を記載してください...',
                                    ),
                                ],
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
                                        style={
                                            'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'},
                                    ),
                                ],
                                className="text-center",
                                width=2,
                                align="center",
                            ),
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        options=select_data(),
                                        id={'type': 'dropdown',
                                            'index': 're_'+row[3]},
                                        placeholder='貢献度...',
                                        value=write_DB.check_contribution(
                                            data[1], row[3]),
                                    ),
                                ],
                                width=8,
                            ),
                            dbc.Col(
                                [
                                    html.Button(
                                        '更新',
                                        id={'type': 'button',
                                            'index': 're_'+row[3]},
                                        style={'background-color': 'red',
                                               }
                                    ),
                                ],
                                width=2,
                            ),
                        ],
                    ),
                ]

        for row in df_request[e_seet4].values:
            if row[3] == node:
                children = [
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        '<説明>',
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
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
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
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
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
                                    ),
                                    dbc.Label(
                                        '<測定B>',
                                        style={'fontSize': 15,
                                               'fontWeight': 'bold'},
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
                                        '<Xの許容範囲>',
                                        style={
                                            'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'},
                                    ),
                                ],
                                className="text-center",
                                width=2,
                                align="center",
                            ),
                            dbc.Col(
                                [
                                    dcc.RangeSlider(
                                        0.00,
                                        1.00,
                                        value=write_DB.check_scope(
                                            data[1], row[3]),
                                        id={'type': 'input',
                                            'index': 're_'+row[3]},
                                        tooltip={
                                            "placement": "bottom", "always_visible": True},
                                        marks={
                                            0: {'label': '0', 'style': {'color': '#77b0b1'}},
                                            0.20: {'label': '0.2'},
                                            0.40: {'label': '0.4'},
                                            0.60: {'label': '0.6'},
                                            0.80: {'label': '0.8'},
                                            1: {'label': '1', 'style': {'color': '#f50'}},
                                        }
                                    ),
                                ],
                                width=8
                            ),
                            html.Br(),
                            html.Hr(),
                        ],
                    ),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label(
                                        '<貢献度入力>',
                                        style={
                                            'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'},
                                    ),
                                ],
                                className="text-center",
                                width=2,
                                align="center",
                            ),
                            dbc.Col(
                                [
                                    dcc.Dropdown(
                                        options=select_data(),
                                        id={'type': 'dropdown',
                                            'index': 're_'+row[3]},
                                        placeholder='貢献度...',
                                        value=write_DB.check_contribution(
                                            data[1], row[3]),
                                    ),
                                ],
                                width=7,
                            ),
                            dbc.Col(
                                [
                                    html.Button(
                                        '更新',
                                        id={'type': 'button',
                                            'index': 're_'+row[3]},
                                        style={'background-color': 'red',
                                               }
                                    ),
                                ],
                                width=2,
                            ),
                        ]
                    ),
                ]
    return children


@callback(
    Output('modal-dismiss', "is_open"),
    Input({'type': 'radio', 'index': ALL}, 'value'),
    Input("close-dismiss", "n_clicks"),
    [State("modal-dismiss", "is_open")],
)
def toggle_modal(radio_list, n2, is_open):
    if radio_list or n2:
        print('dadio', radio_list)
        print(n2)
        radio_num = [value for value in radio_list if value is not None]
        if radio_num == []:
            return is_open
        df_re = pd.read_excel(e_base, sheet_name=[e_seet4])
        for row_2 in df_re[e_seet4].values:
            if row_2[2] == radio_num[0]:
                if row_2[8] == 2:
                    return not is_open
    else:
        return is_open
