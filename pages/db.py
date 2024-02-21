import dash
import dash_bootstrap_components as dbc
from dash import html
from dash.dash_table import DataTable
import pandas as pd
from .core import write_db

#プロジェクト
def read_project(select,pid):
  data=write_db.read_table(select,pid)
  df = pd.DataFrame(data, columns=['pid', 'pname', 'rmax', 'nsprint', 'status'])
  return df

#ノード
def read_qualitynode(select,pid):
  data=write_db.read_table(select,pid)
  df = pd.DataFrame(data, columns=['nid', 'pid', 'cid', 'type', 'subtype','content','achievement'])
  df['content'] = df['content'].astype(str)
  return df

#サポート
def read_support(select):
  data=write_db.read_table(select)
  df = pd.DataFrame(data, columns=['sid','source','destination','contribution'])
  return df

#ページのレイアウト
def db_layout(pid):
  return html.Div(
    [
      dbc.Row(
        [
          dbc.Col(
            [
              html.H5('<Project>'),
              DataTable(
                id='datatable-interactivity',
                columns=[{'name': i, 'id': i} for i in read_project('SELECT * FROM project WHERE pid = %s',pid).columns],
                data=read_project('SELECT * FROM project WHERE pid = %s',pid).to_dict('records'),
                editable=False,
                row_deletable=False,
                filter_action='none',
                sort_action='native',
                sort_mode='multi',
                column_selectable='single',
                row_selectable=False,
                selected_columns=[],
                selected_rows=[],
                page_action='native',
                page_current=0,
                page_size=5,
                style_table={'width': '100%'}
                ),
              html.H5('<support>'),
              DataTable(
                id='datatable-interactivity2',
                columns=[{'name': i, 'id': i} for i in read_support('SELECT * FROM support').columns],
                data=read_support('SELECT * FROM support').to_dict('records'),
                editable=False,
                row_deletable=False,
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                column_selectable='single',
                row_selectable=False,
                selected_columns=[],
                selected_rows=[],
                page_action='native',
                page_current=0,
                page_size=5,
                style_table={'width': '100%'}
                ),
              html.H5('<log>'),
              DataTable(
                id='datatable-interactivity3',
                columns=[{'name': i, 'id': i} for i in read_support('SELECT * FROM log').columns],
                data=read_support('SELECT * FROM log').to_dict('records'),
                editable=False,
                row_deletable=False,
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                column_selectable='single',
                row_selectable=False,
                selected_columns=[],
                selected_rows=[],
                page_action='native',
                page_current=0,
                page_size=10,
                style_table={'width': '100%'}
                )
                
              ]
            ),
          dbc.Col(
            [
              html.H5('<qualitynode>'),
              DataTable(
                id='datatable-interactivity4',
                columns=[{'name': i, 'id': i} for i in read_qualitynode('SELECT * FROM qualitynode WHERE pid = %s',pid).columns],
                data=read_qualitynode('SELECT * FROM qualitynode WHERE pid = %s',pid).to_dict('records'),
                editable=False,
                row_deletable=False,
                filter_action='native',
                sort_action='native',
                sort_mode='multi',
                column_selectable='single',
                row_selectable=False,
                selected_columns=[],
                selected_rows=[],
                page_action='native',
                page_current=0,
                page_size=25,
                style_table={'width': '100%'}
                )
              
              ]
            )
          ]
        )
     
      ]
    )
