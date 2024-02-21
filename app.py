import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output
from urllib.parse import urlparse, parse_qs
from pages import home, edit,create_category,db,dashboard

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


'''
●機能
・システム全体のレイアウト
●id
・url = URL
・page-content = ここに処理をしている
'''
app.layout = html.Div(
  [
    dcc.Location(
      id='url',
      refresh=False
      ),
    dbc.NavbarSimple(
      children = [dbc.NavItem(dbc.NavLink('save/back', href='/home'))],
      brand='Quality Digital Twin',
      color='black',
      dark=True,
      style={'height': '30px'},
      brand_style={'position': 'absolute',
                   'left': '0',
                   'margin-left': '15px'}
      ),
    html.Div(id='page-content')
    ]
  )


#実行ファイルを移す
@app.callback(
  Output('page-content', 'children'),
  Input('url', 'pathname')
  )
def display_page(pathname):
  if pathname == '/':
    return home.home_layout()
  else:
    pathname_part = pathname.split('?')[0]
    parsed_url = urlparse(pathname)
    query_params = parse_qs(parsed_url.query)
    project_name = query_params.get('project_name', [None])[0]
    category_num = query_params.get('category', [None])[0]
    sprint_num = query_params.get('sprint_num', [None])[0]
    state = query_params.get('state', [None])[0]
    pid = query_params.get('pid', [None])[0]
    if pathname_part == '/home':
      return home.home_layout(project_name, category_num)
    elif pathname == '/create_category':
      return create_category.create_category_layout()      
    elif pathname_part =='/edit':
      return edit.edit_layout(project_name, category_num, sprint_num, state, pid)
    elif pathname_part =='/db':
      return db.db_layout(pid)
    elif pathname_part =='/dashboard':
      return dashboard.dashboard_layout(pid,sprint_num,category_num)


if __name__ == '__main__':
    app.run_server(debug=True)
