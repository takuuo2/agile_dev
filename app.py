import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output
from pages import home, edit
import sqlite3

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])


def load_data_from_file():
    conn = sqlite3.connect('log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM logs ORDER BY rowid DESC LIMIT 1")
    latest_row = c.fetchone()
    c.close()
    conn.close()
    print('書き込み',latest_row)
    return latest_row

app.layout = html.Div(
    [
        dcc.Location(
            id='url',
            refresh=False
        ),
        dbc.NavbarSimple(
            children=[
                dbc.NavItem(dbc.NavLink("保存/戻る", href="/home")),
            ],
            brand="Quality Digital Twin",
            color="black",
            dark=True,
            style={'height': '30px'},
            brand_style={'position': 'absolute',
                         'left': '0', 'margin-left': '15px'},
        ),
        html.Div(id='page-content')
    ],
)

# ここに、すべてのページを入れ込む必要がある
@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    print(pathname)
    if pathname == '/home':
        return home.home_layout
    elif pathname == '/edit':
        global h 
        h=load_data_from_file()
        return edit.edit_layout
    else:
        return home.home_layout

if __name__ == '__main__':
    app.run_server(debug=True)
