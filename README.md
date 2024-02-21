# agile_development
・大学のネットワークに入って、実行してください。
　※大学のサーバーの中にある、DBを使用しているため

・データベース変更点
　supportテーブルのsontributionでfloat[0,1]ではなく、integer[0,3]としてます

<<<<<<< HEAD
・実行方法
app.pyを実行してください。
➀プロジェクト名＆カテゴリを入力
➁現在のスプリントをスプリント回数が1以上に変更することにより、各メニュー（Create Category以外）のボタンを押すことが可能
※Create Categoryはプロジェクト名などを入力しなくても押すことが可能

・各ボタン
Sprint Planning:品質状態モデルの編集画面に行くボタン
Dashbard：ダッシュボートを表示するボタン（現在、スプリントの達成度のみ表示可能。もう少し時間ください）
QDT-DB：品質状態モデルを見ることができる
Create Category:QC-DB.db（各重要度のデータベース）を作成することが可能
=======
1/11
・homeからeditまでつながっていないため，URLをhttp://127.0.0.1:8050/editと入力
・edit.pyのL11 data = （何でもよい, project number, sprint number, state, project name, category number)を変更すると自分で編集等できます
>>>>>>> 68b7693edf6cd3e5e03ef0a3d96eac1a8bac4e20
