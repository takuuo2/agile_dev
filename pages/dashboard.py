import dash
from dash import html, dcc, callback
from dash import Input, Output, ALL
import plotly.express as px
import plotly.graph_objects as go
from dash import dash_table
import dash_bootstrap_components as dbc
import pandas as pd
import json
import ast
import re
from itertools import groupby
from decimal import Decimal, ROUND_HALF_UP
import sqlite3
from .core import write_db,node_calculation


#トレンドデータの取得
def getTrend(pid,sprint_num):
  trend_df=[]
  data = []
  columns = ["subchar", "priority", "sprint", "achievement"]
  roots = write_db.getRoots(pid)
  for item in roots:
    subchar = item[0]['subchar']
    priority = item[2]
    achievement = item[1]
    sprint = int(sprint_num)
    data.append([subchar,priority,sprint,achievement])
    nid = item[3]
    while sprint > 1:
      sprint -= 1
      check_achivement=write_db.achievement(nid,sprint)
      if check_achivement == None:
        data.append([subchar,priority,sprint,achievement]) 
      else:
        achievement=check_achivement[0]
        data.append([subchar,priority,sprint,achievement])
  trend_df = pd.DataFrame(data=data, columns=columns)    
  df_sorted = trend_df.sort_values(by='sprint',ascending=True)
  return df_sorted


#達成度の合計を計算
def SumAchievement(trend_df: pd.DataFrame):
  qiu = trend_df["subchar"].unique().tolist()
  achievement = []
  for q in qiu:
    part = trend_df[trend_df["subchar"] == q]
    max_index = part["achievement"].max()
    achievement.append([q, max_index])
  return achievement

#達成度表示を生成
def createAchievementView(trend_df: pd.DataFrame):
  achievement = SumAchievement(trend_df)
  size = len(achievement)
  width = round(35/size)
  list_view = []

  for achieve in achievement:
    lines = trend_df[trend_df["subchar"] == achieve[0]]
    priority = lines.iat[0,1]
    achieve_decimal = Decimal(str(achieve[1])).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    view = html.Div(
      [
        html.P(achieve[0], className="qiu"),
        html.P(str(achieve_decimal) + "%", className="score")
        ],
      className="achievement_container",
      style={
        "width": str(width) + "vw",
        "font-size": str(width*0.3) + "vw",
        "color": px.colors.sequential.Blues[priority+2]
        }
      )
    list_view.append(view)
  return list_view, width

#明度を変えたカラースケールを用意
colors = []
for color in px.colors.qualitative.Set1:
    rgb = re.findall(r"\d+", color)
    new_rgb = []
    for val_str in rgb:
        val = int(val_str)
        val = val*2
        if val > 255:
              val = 255
        new_rgb.append(val)
    colors.append("rgb(" + ",".join(map(str, new_rgb)) + ")")
    

#トレンドグラフを生成
def createTrendBar(trend_df: pd.DataFrame):
  sprint = trend_df["sprint"].nunique()
  bars = []
  lines=[]
  min = 0
  old=0.0
  for i in range(1, sprint+1):
    sprint_df = trend_df[trend_df["sprint"] == i].sort_values("priority", ascending=False).reset_index(drop=True)
    achievement = sprint_df["achievement"].reset_index(drop=True)
    achievement_new =achievement - old 
    bar = go.Bar(
      x=[sprint_df["priority"], sprint_df["subchar"]],
      y=achievement_new,
      name="sprint"+str(i),
      marker={"color": colors[i-1]}
      )
    bars.append(bar)
    old = sprint_df["achievement"].astype(float)
  trend = go.Figure(bars, layout=go.Layout(barmode="stack"))
  trend.update_layout(shapes=lines)

  
  trend.update_layout(
    margin=dict(t=10, b=0, l=20, r=10),
    xaxis=dict(
      dtick=1,
      title={"text": "priority"},
      categoryorder="category descending"
      ),
    yaxis=dict(
      title={"text": "achievement"}
      ),
    legend=dict(
      x=0.5,
      y=-0.2,
      xanchor="center",
      yanchor="top",
      orientation="h"
      )
    )
  return trend


#内訳データの取得
def getBDAchieve(pid,sprint_num):
  nodes = write_db.get_nodes(pid)
  #print(nodes)
  node_dic = []
  columns = ["id", "root", "parent", "label", "value", "status"]
  bd = []
  for node in nodes:
    content_dict = node[5]
    node_dic.append({"NID":node[0], "PID":node[1], "cid": node[2], "type": node[3], "subtype": node[4], 
                     "subchar": content_dict["subchar"], "content": node[5], "achievement": node[6]})
  #print(node_dic)  
  #leaves = write_db.getLeaves(pid)
  
  return None

#ダッシュボードのレイアウト
def dashboard_layout(pid,sprint_num,category_num):
  global testgraph
  global root_dic
  global tables
  testgraph = {}
  root_dic = {}
  tables = {}
  trend_df = getTrend(pid,sprint_num)
  trend = createTrendBar(trend_df)
  achievement, achieve_width = createAchievementView(trend_df)
  bd_df = getBDAchieve(pid,sprint_num)
  #bd_graph = createBDGraph(bd_df)
  #test_df = getTestData()
  #testgraph = createTestGraph(test_df)
  #table_df, root_dic = getTableData()
  #tables = createTables(table_df)
  return html.Div(
    [
      #左側
      html.Div(
        [
          #達成度
          html.Div(
            achievement,
            style={
              'display': 'flex',
              'flex-direction': 'row',
              'justify-content': 'space-around',
              'align-items': 'stretch',
              'padding-left': '5%'
              }
            ),
          html.Div(
            [
              dcc.Graph(
                figure=trend,
                style={
                  'height': '100%',
                  'margin': '5% '
                  },
                )
              ],
            style={'height': '60%'}
            ),
          ],
        className='left'
        ),
          
      #右側
      html.Div(
        [
          #内訳
          html.Div(
            #bd_graph,
            className='bd'
            ),
          #テスト
          html.Div(
            [
              dcc.Graph(
                id='test',
                style={
                  'height': '50vh',
                  'width': '50%'
                  }
                ),
              html.Div(
                id='table',
                style={
                  'height': '50vh',
                  'width': '50%',
                  }
                )
              ],
            className='bottom'
            )
          ],
        className='right'
        )
      ],
    style={
      'display': 'flex'
      }
    )

