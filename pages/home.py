import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output, State
import sqlite3
from .core import write_DB

# カテゴリのプルダウン作成
def dropdown_category():
    conn = sqlite3.connect('./QC_DB.db')
    cursor = conn.cursor()
    cursor.execute('SELECT id, category_name FROM categories')
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    dropdown_normalize = []
    dropdown_normalize = [
        {'label': str(row[1]), 'value': str(row[0])} for row in data
        ]
    return dropdown_normalize

home_layout = html.Div(
    [
        dbc.Row(
            [
                dbc.Col(
                    [
                        html.H1('<Project Information>'),
                        # プロジェクト名の入力
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.P('プロジェクト名：'),
                                    width=2,
                                    className="text-center",
                                    align="center"
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id='project_name',
                                        type='text',
                                        placeholder='プロジェクト名を入力...',
                                        valid=False,
                                        className='mb-3',
                                        style={'width': '80%'}
                                    ),
                                    width=10,
                                ),
                            ],
                            className='mb-3',
                            align='center',
                        ),
                        # カテゴリ入力
                        dbc.Row(
                            [
                                dbc.Col(
                                    html.P('カテゴリ：'),
                                    width=2,
                                    className="text-center",
                                    align="center"
                                ),
                                dbc.Col(
                                    dcc.Dropdown(
                                        id='category_dropdown',
                                        options=dropdown_category(),
                                        multi=False,
                                        placeholder='カテゴリを選択...',
                                        disabled=False,
                                        style={'width': '85%'}
                                    ),
                                    width=10,
                                ),
                            ],
                        ),
                        html.Div(id='check'),
                    ],
                ),

                dbc.Col(
                    [
                        html.H1('<Sprint Information>'),
                        # 現在のスプリントの状態
                        dbc.Row(
                            className='mb-3',
                            align='center',
                            id='sprint_now',
                        ),
                        # 変更場合
                        dbc.Row(
                            className='mb-3',
                            align='center',
                            id='sprint_submit',
                        ),
                    ],
                ),
            ],
        ),
        html.Hr(),
        dbc.Row(
            [
                html.H1('<Menu>'),
                dbc.Row(
                    [
                        dbc.Col(
                            [
                                dbc.Button(
                                    [
                                        html.Span(
                                            " Edit",
                                            style={'font-size': '30px'}
                                        ),
                                        # html.Br(),
                                        html.Span(
                                            "🖊",
                                            style={'font-size': '30px'}
                                        ),
                                    ],
                                    color="secondary",
                                    href="/edit",
                                    id='edit_button',
                                    style={'width': '80%', 'height': '80px'},

                                ),
                            ],
                            width=3,
                            className="text-center",
                            align="center",
                        ),
                        dbc.Col(
                            [
                                dbc.Button(
                                    [
                                        html.Span(
                                            "Dashboard",
                                            style={'font-size': '30px'}
                                        ),
                                        # html.Br(),
                                        html.Span(
                                            "📉",
                                            style={'font-size': '30px'}
                                        ),
                                    ],
                                    color="secondary",
                                    # href="/page-2",
                                    id='dashboard_button',
                                    style={'width': '80%', 'height': '80px'},
                                ),
                            ],
                            width=3,
                            className="text-center",
                            align="center",
                        ),
                        dbc.Col(
                            [
                                dbc.Button(
                                    [
                                        html.Span(
                                            "QDT-DB",
                                            style={'font-size': '30px'}
                                        ),
                                        # html.Br(),
                                        html.Span(
                                            "💾",
                                            style={'font-size': '30px'}
                                        ),
                                    ],
                                    color="secondary",
                                    # href="/page-2",
                                    id='db_button',
                                    style={'width': '80%', 'height': '80px'},
                                ),
                            ],
                            width=3,
                            className="text-center",
                            align="center",
                        ),
                        dbc.Col(
                            [
                                dbc.Button(
                                    [
                                        html.Span(
                                            "Create Category",
                                            style={'font-size': '30px'}
                                        ),
                                        # html.Br(),
                                        html.Span(
                                            "🖥️",
                                            style={'font-size': '30px'}
                                        ),
                                    ],
                                    color="secondary",
                                    style={'width': '80%', 'height': '80px'},
                                ),
                            ],
                            width=3,
                            className="text-center",
                            align="center",
                        ),
                    ],
                ),
            ],
        ),
        dcc.Store(id='data-store', storage_type='session'),
    ],
)

# カテゴリの入力制限解除
@callback(
    Output('category_dropdown', 'disabled'),
    Input('project_name', 'value')
)
def disable_input_1(input1_value):
    return not input1_value

# スプリントを確認
@callback(
    Output('sprint_now', 'children'),
    Output('sprint_submit', 'children'),
    Input('category_dropdown', 'value'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def check(category, pname):
    if category is None or category == '':
        return None

    else:
        project = write_DB.check_project(pname)
        if project == 'none':
            sprint = '-'
            state = '-'
            sprint_value = 1
            state_value = 'planning'
        else:
            sprint = project[1]
            state = project[2]
            sprint_value = project[1]
            state_value = project[2]

        now_children = [
            dbc.Col(
                html.P('現在⇒'),
                width=2,
                className="text-center",
                align="center"
            ),
            dbc.Col(
                html.P('スプリント回数：'),
                width=2,
                className="text-center",
                align="center"
            ),
            dbc.Col(
                html.P(sprint, id='sprint_view'),
                width=1,
                className="text-center",
                align="center"
            ),
            dbc.Col(
                html.P('状態：'),
                width=1,
                className="text-center",
                align="center"
            ),
            dbc.Col(
                html.P(state, id='state_view'),
                width=2,
                className="text-center",
                align="center"
            ),

        ]
        chenge_children = [
            dbc.Col(
                html.P('変更する場合⇒'),
                width=2,
                className="text-center",
                align="center"
            ),
            dbc.Col(
                html.P('スプリント回数：'),
                width=2,
                className="text-center",
                align="center"
            ),
            dbc.Col(
                dcc.Input(
                    id="sprint",
                    type="number",
                    placeholder=sprint_value,
                    style={'width': '85%'}
                ),
                width=1,
            ),
            dbc.Col(
                html.P('状態：'),
                width=1,
                className="text-center",
                align="center"
            ),
            dbc.Col(
                dcc.Dropdown(
                    ['planning', 'doing', 'reviewing'],
                    placeholder=state_value,
                    id='state',
                ),
                width=2,
            ),
            dbc.Col(
                html.Button('更新', id='submit', n_clicks=0),
                width=1,
            ),
        ]
        return now_children, chenge_children

# スプリントの更新
@callback(
    Output('sprint_view', 'children'),
    Output('state_view', 'children'),
    Input('submit', 'n_clicks'),
    State('state', 'value'),
    State('sprint', 'value'),
    State('project_name', 'value'),
    prevent_initial_call=True
)
def updata(n_click, state, sprint, pname):
    if n_click == 0:
        return dash.no_update, dash.no_update
    else:
        if state is not None and sprint is not None:
            write_DB.write_project(pname, sprint, state)
            return sprint, state
        else:
            return '入力エラー', '入力エラー'

# ボタンの操作
@callback(
    Output('edit_button', 'disabled'),
    Output('dashboard_button', 'disabled'),
    Output('db_button', 'disabled'),
    Output('data-store', 'data'),
    Input('project_name', 'value'),
    Input('category_dropdown', 'value'),
)
def disable_button(project_name, category):     
    if project_name is not None and category is not None:
        project = write_DB.check_project(project_name)
        if project == 'none':
            write_DB.write_project(project_name, 1, 'planning')
            print('OK')
        project = write_DB.check_project(project_name) + (project_name,)
        print('OK')
        print(project)
        save_data_to_file(project[0],project[1],project[2],project[3],category)
        return False, False, False,project
    return True, True, True, None
    
def save_data_to_file(pid,nsprint,state,pname,category):
    # SQLiteデータベースに接続
    conn = sqlite3.connect('log.db')

    # テーブルの作成
    cursor = conn.cursor()

    # categoriesテーブルが存在しない場合は作成
    create_logs_table_query = '''
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY,
        pid INTEGER,
        nsprint INTEGER,
        state TEXT NOT NULL,
        pname TEXT NOT NULL,
        category TEXT NOT NULL
    );
    '''
    cursor.execute(create_logs_table_query)

    cursor.execute('INSERT INTO logs (pid,nsprint,state,pname,category) VALUES (?,?,?,?,?)', (pid,nsprint,state,pname,category))
    conn.commit()
    
    # データベースとの接続を閉じる
    cursor.close()
    conn.close()
    return None
