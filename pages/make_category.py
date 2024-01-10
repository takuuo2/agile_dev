import dash
import dash_bootstrap_components as dbc
from dash import html, dcc, callback
from dash.dependencies import Input, Output,State
import sqlite3

home_layout = html.Div(
    [
        dbc.Col(
            [
                html.H1('<create category>'),
                    
            ]
        )
        ],
    ),
                