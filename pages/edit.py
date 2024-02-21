import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State, ALL
from matplotlib import category
import pandas as pd
import re
from .core import write_db,node_calculation
import plotly.graph_objs as go
import sqlite3


#Excelのファイル名とシート名
e_base = '保守性_DB.xlsx'
e_square = 'SQuaRE'
e_maintainability = 'maintainability'
e_architecture = 'architecture'
e_request = 'request'


#データの読み取り
df_square = pd.read_excel(e_base, sheet_name=[e_square])
df_maintainability = pd.read_excel(e_base, sheet_name=[e_maintainability])
df_architecture = pd.read_excel(e_base, sheet_name=[e_architecture])
df_request = pd.read_excel(e_base, sheet_name=[e_request])


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
    textinfo='none',  
    hoverinfo='none',
    marker=dict(colors=[colors[1], 'rgba(0,0,0,0)'],
                line=dict(color='black', width=1))
    )
  trace_current = go.Pie(
    labels=labels,
    values=current,
    hole=0,
    sort=False,
    textinfo='none',  
    hoverinfo='none',
    marker=dict(colors=[colors[0], 'rgba(0,0,0,0)'],
                line=dict(color='black', width=1))
    )
  figure = go.Figure(data=[trace_previous, trace_current])
  figure.update_layout(
    showlegend=False,
    plot_bgcolor='rgba(0,0,0,0)',
    paper_bgcolor='rgba(0,0,0,0)',
    font=dict(size=9),
    autosize=False,
    height=37,
    width=37,
    margin=dict(l=1, r=1, t=1, b=1),
    )
  return figure


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
      for child in node.children:
        total_contribution += child.contribution
        child_name += [child.id]
        child_contribution += [child.contribution]
      for x, y in zip(child_name, child_contribution):
        tree_name += [x]
        tree_contribution += [round(y/total_contribution*100)]
      for child in node.children:
        calculate_contribution_percentage(child, x=1)
    return 0
  else:
    for x, y in zip(tree_name, tree_contribution):
      if x == node:
        return y


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


# 貢献度を検索
def search(category_num, node):
    conn = sqlite3.connect('QC_DB.db')
    cursor = conn.cursor()
    # テーブルからデータを取得
    cursor.execute(
        'SELECT importance FROM subcategories WHERE category_id = ? AND third_name = ?', (category_num, node))
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    re_data = data[0]
    return chenge_int(re_data[0])

# カテゴリのプルダウンの作成
def dropdown_sub(category_num, SQuaRE_name):
  options = []
  list = ('H', 'M', 'L', 'N')
  color_list = ('red', 'orange', 'LightGreen', 'MediumTurqoise')
  conn = sqlite3.connect('QC_DB.db')
  cursor = conn.cursor()
  cursor.execute('SELECT third_name, importance FROM subcategories WHERE category_id = ? AND second_name = ?', (category_num,SQuaRE_name,))
  data = cursor.fetchall()
  cursor.close()
  conn.close()
  x = 0
  for i in list:
    for num in data:
      if num[1] == i:
        options.append({'label': html.Div(num[0], style={'color': color_list[x], 'font-size': 15}),'value': num[0]})
    x = x+1
  return options


# 要求文の作成
def make_request(node, node_data):
  options = []
  new_options = []
  for row in df_request[e_request].values:
    if row[1] == node:
      options += [{'label': row[2],'value': row[2]}]
  new_options = [dict(t) for t in {tuple(d.items()) for d in options}]
  if node_data.children is not None:
    for children in node_data.children:
      for row in df_request[e_request].values:
        if row[3] == children.id or row[7] == children.id:
          for option in new_options:
            label = option['label']
            if label == row[2]:
              option['disabled'] = True
      if children.id == '修正量の低減':
        for row_2 in df_request[e_request].values:
          if row_2[8] == 2:
            for option in new_options:
              label = option['label']
              if label == row_2[2]:
                option['disabled'] = True
          
  return new_options


#各名称の作成
def make_adovaic_node(node):
  options = []
  options += [
        {
          'label': html.Div('<品質実現>', style={'font-size': 15}),
          'value': 0,
          'disabled': True
          }
        ]
  for row in df_request[e_request].values:
    if row[2] == node:
      for ri in df_architecture[e_architecture].values:
        if ri[3] == row[7]:
          options += [
            {
              'label': html.Div(ri[3], style={'font-size': 15}),
              'value': ri[3]
              }
            ]
  options += [
    {
      'label': html.Div('<品質活動>', style={'font-size': 15}),
      'value': 0,
      'disabled': True
      }
    ]
  for row in df_request[e_request].values:
    if row[2] == node:
      options += [
        {
          'label': html.Div(row[3], style={'font-size': 15}),
          'value': row[3]
          }
        ]
  return options


# 各名称の作成_子供あり
def make_adovaic_node_children(node, node_data):
  options = []
  for row in df_request[e_request].values:
    if row[3] == node or row[7] == node:
      options += [{'label': html.Div('<品質実現>', style={'font-size': 15}),'value': 0,'disabled': True}]
      for ri in df_architecture[e_architecture].values:
        if ri[3] == row[7]:
          options += [{'label': html.Div(ri[3], style={'font-size': 15}),'value': ri[3]}]
      options += [{'label': html.Div('<品質活動>', style={'font-size': 15}),'value': 0,'disabled': True}]
      options += [{'label': html.Div(row[3], style={'font-size': 15}),'value': row[3]}]
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

def make_adovaic_node_children_1(node_data):
  options = []
  new_options = []
  for row in df_request[e_request].values:
    if row[8] == 2:
      options += [{'label': row[2],'value': row[2]}]
  new_options = [dict(t) for t in {tuple(d.items()) for d in options}]
  if node_data.children is not None:
    for children in node_data.children:
      for row in df_request[e_request].values:
        if row[3] == children.id or row[7] == children.id:
          for option in new_options:
            label = option['label']
            if label == row[2]:
              option['disabled'] = True
  return new_options

# 貢献度のプルダウンデータ
def select_data():
  data = [
    {'label': '貢献度：高', 'value': '3'},
    {'label': '貢献度：中', 'value': '2'},
    {'label': '貢献度：低', 'value': '1'},
    {'label': '貢献度：不要', 'value': '0'}
    ]
  return data

#左の作成
def message_display(node,pid):
  if node is None:
    return None
  else:
    children = []
    for row in df_architecture[e_architecture].values:
      if row[3] == node:
        children = [
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<基本戦略>',style={'fontSize': 15,'fontWeight': 'bold'})
                  ],
                className='text-center',
                width=2,
                align='center'),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[1]),id='ar_base')
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<個別戦略>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[2]),id='ar_in'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<説明>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center',
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[4]),id='ar_exa')
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<前提条件>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[5]),id='ar_tec'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<実現例>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[6]),id='ar_tec'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<実現手法入力>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'}),
                  ],
                className='text-center',
                width=2,
                align='center',
                ),
              dbc.Col(
                [
                  dbc.Input(id={'type': 'input','index': 're_'+row[3]},
                            type='text',
                            value=write_db.check_description(pid, row[3]),
                            placeholder='手法を記載してください...',
                            )
                  ]
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<貢献度入力>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  dcc.Dropdown(
                    options=select_data(),
                    id={'type': 'dropdown','index': 're_'+row[3]},
                    placeholder='貢献度...',
                    value=write_db.check_contribution(pid, row[3])
                    )
                  ],
                width=8,
                ),
              dbc.Col(
                [
                  html.Button(
                    '更新',
                    id={'type': 'button','index': 're_'+row[3]},
                    style={'background-color': 'red'}
                    )
                  ],
                width=2
                )
              ]
            )
          ]
        return children
    for row in df_request[e_request].values:
      if row[3] == node:
        children = [
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<説明>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[4]),id='re_exa'),
                  ],
                width=10
                ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<測定機能>',style={'fontSize': 15,'fontWeight': 'bold'})
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  html.P(insert_line_breaks(row[5]),id='re_ex')
                  ],
                width=5
                ),
              dbc.Col(
                [
                  dbc.Label('<測定A>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  dbc.Label('<測定B>',style={'fontSize': 15,'fontWeight': 'bold'}),
                  ],
                width=1
                ),
              dbc.Col(                                
                      [
                        html.P('他研究A',id='re_a'),
                        html.P('他研究B',id='re_b')
                        ],
                      width=4
                      ),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(  
                [   
                  dbc.Label('<Xの許容範囲>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'})
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  dcc.RangeSlider(
                    0.00,
                    1.00,
                    value=write_db.check_scope(pid, row[3]),
                    id={'type': 'input','index': 're_'+row[3]},
                    tooltip={'placement': 'bottom', 'always_visible': True},
                    marks={
                      0: {'label': '0', 'style': {'color': '#77b0b1'}},
                      0.20: {'label': '0.2'},
                      0.40: {'label': '0.4'},
                      0.60: {'label': '0.6'},
                      0.80: {'label': '0.8'},
                      1: {'label': '1', 'style': {'color': '#f50'}}
                      }
                    )
                  ],
                width=8
                ),
              html.Br(),
              html.Hr()
              ]
            ),
          dbc.Row(
            [
              dbc.Col(
                [
                  dbc.Label('<貢献度入力>',style={'fontSize': 15, 'fontWeight': 'bold', 'color': 'red'}),
                  ],
                className='text-center',
                width=2,
                align='center'
                ),
              dbc.Col(
                [
                  dcc.Dropdown(
                    options=select_data(),
                    id={'type': 'dropdown','index': 're_'+row[3]},
                    placeholder='貢献度...',
                    value=write_db.check_contribution(pid, row[3])
                    )
                  ],
                width=7
                ),
              dbc.Col(
                [
                  html.Button(
                    '更新',
                    id={'type': 'button','index': 're_'+row[3]},
                    style={'background-color': 'red'}
                    )
                  ],
                width=2
                )
              ]
            )
          ]
        break
    return children


#品質状態モデル表示の画面
def tree_display(node, category, pid,indent=''):
  if node is None:
    return None
  else:
    if node.type != 'QRM':
      aim_node = write_db.check_node(pid,node.id)
      before = write_db.check_achievement_old(pid, node.id)
      now = aim_node[6]
      com = '達成:'+str(now)+'%'
    if node.type == 'REQ':
      if node.id == '保守性':
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node)) + '%' + ']', style={'display': 'none', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('品質要求', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                dbc.Popover(dbc.RadioItems(options=dropdown_sub(category, node.id),
                                           id={'type': 'radio', 'index': node.id}),
                            target={'type': 'button','index': node.id},
                            body=True,
                            trigger='hover'),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}),
                ]
              )
            ],
          open=True
          )
      else:
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('品質要求', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                dbc.Popover(dbc.RadioItems(options=make_request(node.id, node),
                                           id={'type': 'radio', 'index': node.id}),
                            target={'type': 'button','index': node.id},
                            body=True,
                            trigger='hover',
                            ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
    elif node.type == 'IMP':
      ver = 0
      for row in df_request[e_request].values:
        if row[7] == node.id:
          ver = row[8]
          text = row[2]
          break
      if ver == 1 :
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文:', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children(node.id, node),
                                           id={'type': 'radio','index': node.id}),
                            id='popover',
                          target={'type': 'button','index': 'ex'+node.id},
                          body=True,
                          trigger='hover',
                          ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
        tree.children.append(
          html.Details(
            [
              html.Summary(
                [
                  html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                  html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                  html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                  html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before, now),
                    config={'displayModeBar': False}
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                         )
                  ]
                ),
              html.P('実現手法：' + str(node.other),style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            )
          )
      elif ver == 2:
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[＋'+row[9]+']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文:', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children(node.id, node),
                                           id={'type': 'radio','index': node.id}),
                            id='popover',
                          target={'type': 'button','index': 'ex'+node.id},
                          body=True,
                          trigger='hover',
                          ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
        tree.children.append(
          html.Details(
            [
              html.Summary(
                [
                  html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                  html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                  html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                  html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before, now),
                    config={'displayModeBar': False}
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                         )
                  ]
                ),
              html.P('実現手法：' + str(node.other),style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            )
          )
      else:
        if node.id == '修正量の低減':
          tree = html.Details(
            [
              html.Summary(
                [
                  html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={
                    'display': 'inline-block','fontSize': 12, 'marginRight': '10px'}),
                  html.P('【下記要求2つで実現】', style={
                    'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                  html.Button(node.id, id='修正量の低減', style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                  dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children_1(node),
                                           id={'type': 'radio','index': node.id}),
                            id='popover',
                          target='修正量の低減',
                          body=True,
                          trigger='hover',
                          ),
                  html.P(com, style={
                    'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before, now),
                    config={'displayModeBar': False},
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                         )
                  ]
                )
              ],
            style={'margin-left': '15px'}
            )
        elif node.id == 'テスト自動化':
          for row_3 in df_request[e_request].values:
            if row_3[8] == 3:
              resul = row_3[9].split(',')
              text= row_3[2]
              break
          arc_subchar =[]
          arc_descriptiom =[]
          arc_achivement =[]
          req_subchar =[]
          req_tolerance =[]
          req_achivement =[]
          message =[]
          before_achivement =[]
          for row_4 in df_request[e_request].values:
            for x in resul:
              if row_4[7] == x:
                message +=[row_4[2]]
                no_arc =write_db.check_node(pid,row_4[7])
                arc_subchar +=[no_arc[5]['subchar']]
                arc_descriptiom +=[no_arc[5]['description']]
                arc_achivement +=[no_arc[6]]
                no_req = write_db.check_node(pid,row_4[3])
                req_subchar +=[no_req[5]['subchar']]
                req_tolerance +=[no_req[5]['tolerance']]
                req_achivement +=[no_req[6]]
                before_achivement +=[write_db.check_achievement_old(pid,row_4[7])]
                before_achivement +=[write_db.check_achievement_old(pid,row_4[3])]
          tree = html.Details(
            [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文:', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),
                                 config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              ),
            html.Details(
              [
                html.Summary(
                  [
                    html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                    html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                    html.Button(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                    html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                    html.P(dcc.Graph(
                      figure=make_data(before, now),
                      config={'displayModeBar': False}
                      ),
                           style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                    ]
                  ),
                html.Details(
                  [
                    html.Summary(
                      [
                        html.P('[50%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                        html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                        html.Button(message[0], style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                        html.P('達成:'+str(arc_achivement[0])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                        html.P(dcc.Graph(
                          figure=make_data(before_achivement[0], arc_achivement[0]),
                          config={'displayModeBar': False},
                          ),
                              style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                                  'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                        ]
                      ),
                    html.Details(
                  [
                    html.Summary(
                      [
                        html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                        html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                        html.Button(arc_subchar[0], id={'type': 'button', 'index': arc_subchar[0]}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                        html.P('達成:'+str(arc_achivement[0])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                        html.P(dcc.Graph(
                          figure=make_data(before_achivement[0], arc_achivement[0]),
                          config={'displayModeBar': False}
                          ),
                              style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                              )
                        ]
                      ),
                    html.P('実現手法：' + arc_descriptiom[0],style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
                    html.Details(
                      [
                        html.Summary(
                          [
                            html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                            html.P('品質活動', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                            html.Button(req_subchar[0], id={'type': 'button', 'index': req_subchar[0]}, style={
                                                        'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                            html.P('達成:'+str(req_achivement[0])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                            html.P(dcc.Graph(figure=make_data(before_achivement[1],req_achivement[0] ),config={'displayModeBar': False}),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                        'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                            ]
                          ),
                        html.P('許容範囲：' + str(req_tolerance[0]),
                                            style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                        ],
                      style={'margin-left': '15px'}
                      )
                    ],
                  style={'margin-left': '15px', 'marginBottom': '5px'}
                  )
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            ),
            html.Details(
              [
                html.Summary(
                  [
                  html.P('[50%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                  html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '5px', 'fontSize': 10}),
                  html.Button(message[1], style={'display': 'inline-block', 'marginRight': '1px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline'}),
                  html.P('達成:'+str(arc_achivement[1])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                  html.P(dcc.Graph(
                    figure=make_data(before_achivement[2], arc_achivement[1]),
                    config={'displayModeBar': False},
                    ),
                         style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                            'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                  ]
                ),
                html.Details(
                  [
                    html.Summary(
                      [
                        html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                        html.P('品質実現', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                        html.Button(arc_subchar[1], id={'type': 'button', 'index': arc_subchar[1]}, style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                        html.P('達成:'+str(arc_achivement[1])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                        html.P(dcc.Graph(
                          figure=make_data(before_achivement[2], arc_achivement[1]),
                          config={'displayModeBar': False}
                          ),
                              style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top','margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                              )
                        ]
                      ),
                    html.P('実現手法：' + arc_descriptiom[1],style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
                    html.Details(
                      [
                        html.Summary(
                          [
                            html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                            html.P('品質活動', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                            html.Button(req_subchar[1], id={'type': 'button', 'index': req_subchar[1]}, style={
                                                        'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                            html.P('達成:'+str(req_achivement[1])+'%', style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                            html.P(dcc.Graph(figure=make_data(before_achivement[3],req_achivement[1] ),config={'displayModeBar': False}),
                                    style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                                        'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                            ]
                          ),
                        html.P('許容範囲：' + str(req_tolerance[1]),
                                            style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
                        ],
                      style={'margin-left': '15px'}
                      )
                    ],
                  style={'margin-left': '15px', 'marginBottom': '5px'}
                  )
              ],
            style={'margin-left': '15px', 'marginBottom': '5px'}
            ),
            ],
          style={'margin-left': '15px'}
          )
 
                    ],
          open=True,
          style={'margin-left': '15px'}
          )
            
                
    elif node.type == 'ACT':
      if node.parent.type != 'IMP':
        text = ''
        for row in df_request[e_request].values:
          if row[3] == node.id:
            text = row[2]
            break
        tree = html.Details(
          [
            html.Summary(
              [
                html.P('[' + str(calculate_contribution_percentage(node.id)) + '%' + ']', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 10}),
                html.Button(text, id={'type': 'button', 'index': 'ex'+node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'border': 'none', 'textDecoration': 'underline' }),
                dbc.Popover(dbc.RadioItems(options=make_adovaic_node_children(node.id, node),id={'type': 'radio', 'index': node.id}),
                            id='popover',
                            target={'type': 'button','index': 'ex'+node.id},
                            body=True,
                            trigger='hover'
                            ),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                       )
                ]
              )
            ],
          open=True,
          style={'margin-left': '15px'}
          )
        tree.children.append(html.Details(
          [
            html.Summary(
              [
                html.P('[100%]', style={'display': 'inline-block', 'fontSize': 12, 'marginRight': '10px'}),
                html.P('品質活動', style={'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                                            'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                html.P(com, style={'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(figure=make_data(before, now),config={'displayModeBar': False}),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'})
                ]
              ),
            html.P('許容範囲：' + str(node.other),
                               style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
            ],
          style={'margin-left': '15px'}
          )
        )
      else:
        tree= html.Details(
          [
            html.Summary(
              [
                html.P('[100%]', style={
                  'display': 'inline-block', 'fontSize': 12, 'marginRight': '2px', 'marginRight': '10px'}),
                html.P('品質活動', style={
                  'display': 'inline-block', 'marginRight': '10px', 'border': '1px solid #000000', 'fontSize': 10}),
                html.Button(node.id, id={'type': 'button', 'index': node.id}, style={
                  'display': 'inline-block', 'marginRight': '10px', 'fontSize': 13, 'background': 'none', 'fontWeight': 'bold', 'border': 'none'}),
                html.P(com, style={
                  'display': 'inline-block', 'marginRight': '3px', 'fontSize': 11}),
                html.P(dcc.Graph(
                  figure=make_data(before, now),
                  config={'displayModeBar': False}
                  ),
                       style={'display': 'inline-block', 'width': '0%', 'verticalAlign': 'top',
                                           'margin': '0', 'position': 'relative', 'top': '0px', 'textAlign': 'center'}
                       )
                ]
              ),
            html.P('許容範囲：' + str(node.other),
                   style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'}),
            html.P('測定値：' + str(0.40),
                               style={'display': 'block', 'fontSize': 12, 'margin-left': '30px'})
            ],
          style={'margin-left': '30px'}
          )

    elif node.type == 'QRM':
      tree = html.Details(
        [
          html.Summary(
            [
               html.P('PQ要求文：', style={'display': 'inline-block', 'marginRight': '10px', 'fontSize': 10}),
               html.Span(node.id, id={'type': 'button', 'index': node.id}, style={'display': 'inline-block', 'marginRight': '15px', 'textDecoration': 'underline', 'fontSize': 12}),
               dbc.Popover(dbc.RadioItems(options=make_adovaic_node(node.id),
                                          id={'type': 'radio', 'index': node.id}
                                          ),
                           id='popover',
                           target={'type': 'button','index': node.id},
                           body=True,
                           trigger='hover',
                           )
              ]
            )
          ],
        open=True,
        style={'margin-left': '15px'}
        )
    if node.children:
      children = [tree_display(child, category,pid,indent + '　')for child in node.children]
      tree.children.append(html.Div(children))

  return tree


'''
●機能：
・編集画面のレイアウト
●id:
・select = 品質モデルの利用者から見えるモデル
・model_free = 品質状態モデルを表示する
・right_free = データを表示する
'''
def edit_layout(project_name, category_num, sprint_num, state, pid):
  return dbc.Container(
   [
      dbc.Row(
        [
          dbc.Col(
            [
              html.Div(
                [
                  dbc.Row(
                    [
                      html.H5('project', style={'flex-direction': 'column', 'backgroundColor': '#2d3748','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      html.P('project:', style={'display': 'inline-block', 'width': '70px'}),
                      html.P(project_name, style={'display': 'inline-block', 'width': '200px'}),
                      html.P('sprint:', style={'display': 'inline-block', 'width': '70px'}),
                      html.P(sprint_num, style={'display': 'inline-block', 'width': '30px'}),
                      html.P(state, style={'display': 'inline-block', 'width': '100px'}),
                      ]
                    ),
                  dbc.Row(
                    [
                      html.H5('setting', style={'flex-direction': 'column', 'backgroundColor': '#2d3748','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      ]
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
                        labelStyle={'display': 'flex','align-items': 'center','width': '100%','background-color': 'white','marginRight': '20px'}
                        )     
                      ],
                    style={'margin': '0', 'background-color': 'white'}
                    )
                  ]
                )
              ],
            width=2
            ),
          dbc.Col(
            [
              html.Div(
                [
                  dbc.Row(
                    [
                      html.H5('model', style={'flex-direction': 'column', 'backgroundColor': 'black','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      ]
                    ),
                  dbc.Row(
                    id='model_free',
                    style={'overflow': 'scroll','overflowX': 'scroll','overflowY': 'scroll', 'height': '90vh', 'whiteSpace': 'nowrap', 'overflowWrap': 'normal'}
                    )
                  ]
                )
              ], 
            width=3, className='bg-light'),
          dbc.Col(
            [
              html.Div(
                [
                  dbc.Row(
                    [
                      html.H5('Quality condition model',style={'flex-direction': 'column', 'backgroundColor': '#2d3748','color': 'white', 'text-align': 'center', 'height': '4vh'}),
                      ]
                    ),
                  dbc.Row(
                    id='right_free',
                    )
                  ]
                )
              ],
            width=7)
          ],
        style={'height': '95vh'}
        )
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
  State({'type': 'dropdown', 'index': ALL}, 'value'),
  State('url', 'pathname'),
  prevent_initial_call=True
)
def up_node(input_value, button_list, radio_list, input_list, drop_list,url):
  
  if input_value is None:
    return dash.no_update,dash.no_update
  else:
    match = re.search(r'pid=(\d+)', url)
    match1 = re.search(r'category=(\d+)', url)
    if match and match1:
      pid = match.group(1)
      category = match1.group(1)
    #保守性が選ばれたとき
    if (button_list == []) and (radio_list == []) and (input_list == []) and (drop_list == []):
      check_node = write_db.check_node(pid,input_value)
      if check_node == 'none':
        for row in df_square[e_square].values:
          if row[1] == input_value:
            write_db.write_node(pid, row[1], 'REQ', 'qiu', {'subchar': row[1], 'statement': row[2]}, 1, 0, 0)
            break
      node = node_calculation.create_tree(pid, input_value) 
      return tree_display(node,category,pid),dash.no_update
    #トップオーバーが選択されたとき
    elif (input_list == []) and (drop_list == []):
      radio_num = [value for value in radio_list if value is not None]
      button_check = [value for value in button_list if value is not None]      
      if button_check == []:
        for row in df_maintainability[e_maintainability].values:
          if row[1] == radio_num[0]:
            check_node = write_db.check_node(pid,radio_num[0])
            if check_node == 'none':
              write_db.write_node(pid, row[1], 'REQ', 'qiu', {'subchar': row[1], 'statement': row[2]}, search(category, radio_num[0]),write_db.check_node(pid, input_value)[0],0.0) 
            node = node_calculation.make_tree(pid, input_value)
            return tree_display(node,category,pid), dash.no_update
        for row in df_request[e_request].values:
          if row[2] == radio_num[0]:
            if row[8] == 1 or row[8] == 2:
              node1 = node_calculation.make_tree(pid, '保守性')
              node = node_calculation.add_child_to_node(node1, row[1], row[2], 1, 1, 'QRM')
              return tree_display(node,category,pid), dash.no_update
            else:
              result = row[9].split(',')
              for ri in df_request[e_request].values:
                for x in result:
                  if ri[7]==x:
                    check_ar = write_db.check_node(pid, ri[7])
                    check_re = write_db.check_node(pid, ri[3])     
                    if check_ar == 'none' or check_re == 'none':
                      return dash.no_update, ['QP要求文：['+ri[2]+']　'+'の品質実現または，品質活動が未設定のため，追加できません']
              node1 = node_calculation.make_tree(pid, input_value)
              node = node_calculation.add_child_to_node(node1, row[1], radio_num[0], 1, 1, 'QRM')
              return tree_display(node,category,pid), dash.no_update
        return dash.no_update, message_display(radio_num[0],pid)
      else:
        ctx = dash.callback_context
        triggered_id = ctx.triggered_id
        button_id = triggered_id['index']
        for row in df_architecture[e_architecture].values:
          if row[3] == button_id:
            return dash.no_update, message_display(button_id,pid)
        for row in df_request[e_request].values:
          if row[3] == button_id:
            return dash.no_update, message_display(button_id,pid)
        node = node_calculation.make_tree(pid, input_value)
        return tree_display(node,category,pid),dash.no_update
    #更新されたとき
    else:
      radio_num = [value for value in radio_list if value is not None]
      button_check = [value for value in button_list if value is not None]
      if button_check == []:
        return dash.no_update, dash.no_update
      ctx = dash.callback_context
      triggered_id = ctx.triggered_id
      button_id = triggered_id['index']
      if button_id[:3] == 're_':
        index = button_id.index('re_') + len('re_')
        rest_of_text = button_id[index:]
        input_num = [value for value in input_list if value is not None]
        if input_num == []:
          input_num += ['未記入']
        #アーキテクチャの書き込み
        for row1 in df_architecture[e_architecture].values:
          if row1[3] == rest_of_text:
            for row2 in df_request[e_request].values:
              if row2[7] == rest_of_text:
                if row2[8] == 1 :
                  child_node = write_db.check_node(pid,row2[3])
                  if child_node == 'none':
                    write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], write_db.check_node(pid, row1[7])[0],0.0)
                    node = node_calculation.make_tree(pid, input_value)
                    return tree_display(node,category,pid), []
                  else:
                    write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], write_db.check_node(pid, row1[7])[0],0.0,child_node[0])
                    node = node_calculation.make_tree(pid, input_value)
                    return tree_display(node,category,pid), []
                elif row2[8] == 2 :
                  parent_node = write_db.check_node(pid,'修正量の低減')
                  if parent_node == 'none':
                    write_db.write_node(pid, '修正量の低減', 'IMP', 'arch', {'subchar': '修正量の低減', 'description': '以下で実現'}, 1, write_db.check_node(pid, row1[7])[0],0.0)
                    write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], write_db.check_node(pid, '修正量の低減')[0],0.0)
                    node = node_calculation.make_tree(pid, input_value)
                    return tree_display(node,category,pid), []
                  else:
                    child_node = write_db.check_node(pid,row2[3])
                    if child_node == 'none':
                      write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], parent_node[0],0.0)
                      node = node_calculation.make_tree(pid, input_value)
                      return tree_display(node,category,pid), []
                    else:
                      write_db.write_node(pid, rest_of_text, 'IMP', 'arch', {'subchar': rest_of_text, 'description': input_num[0]}, drop_list[0], parent_node[0],0.0,child_node[0])
                      node = node_calculation.make_tree(pid, input_value)
                      return tree_display(node,category,pid), []
          else:
            continue
        #品質活動
        for row_1 in df_request[e_request].values:
          if row_1[3] == rest_of_text:
            if row_1[8] == 1:
              parent_node =write_db.check_node(pid,row_1[7])
              if parent_node == 'none':
                write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], write_db.check_node(pid, row_1[1])[0],0.0)
                node = node_calculation.make_tree(pid, input_value)
                return tree_display(node,category,pid), []
              else:
                write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], parent_node[0],0.0)
                node = node_calculation.make_tree(pid, input_value)
                return tree_display(node,category,pid), []
            elif row_1[8]== 2:
              parent_node =write_db.check_node(pid,row_1[7])
              if parent_node == 'none':
                pare_parent_node =write_db.check_node(pid,'修正量の低減')
                if pare_parent_node == 'none':
                  write_db.write_node(pid, '修正量の低減', 'IMP', 'arch', {'subchar': '修正量の低減', 'description': '以下で実現'}, 1, write_db.check_node(pid, row_1[1])[0],0.0)
                  write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], write_db.check_node(pid, '修正量の低減')[0],0.0)
                  node = node_calculation.make_tree(pid, input_value)
                  return tree_display(node,category,pid), []
                else:
                  write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], pare_parent_node[0],0.0)
                  node = node_calculation.make_tree(pid, input_value)
                  return tree_display(node,category,pid), []
              else:
                write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], parent_node[0],0.0)
                node = node_calculation.make_tree(pid, input_value)
                return tree_display(node,category,pid), []
            else:
              write_db.write_node(pid, 'テスト自動化', 'IMP', 'arch', {'subchar': 'テスト自動化', 'description': '以下で実現'}, drop_list[0], write_db.check_node(pid, row_1[1])[0],0.0)
              write_db.write_node(pid, rest_of_text, 'ACT', 'sa', {'subchar': rest_of_text, 'tolerance': input_num[0]}, drop_list[0], write_db.check_node(pid, 'テスト自動化')[0],0.0)
              node = node_calculation.make_tree(pid, input_value)
              return tree_display(node,category,pid), []
          else:
            continue
    return dash.no_update,dash.no_update
    