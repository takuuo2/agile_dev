import psycopg2
from psycopg2 import Error
import json

#projectテーブルの確認
def check_project(pname):
    try:
        connector = psycopg2.connect(
            'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                user="postgres",        # ユーザ名
                password="selab",      # パスワード
                host="172.21.40.30",   # ホスト名
                port="5432",           # ポート番号
                dbname="QDT-DB"
                )
            )      
        cursor = connector.cursor()
        check_query = "SELECT pid, nsprint, status FROM project WHERE pname = %s"
        cursor.execute(check_query, (pname,))
        existing_pid = cursor.fetchone()
        if existing_pid:
            message=existing_pid
        else:
            message='none'
            
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    
    return message

#projectテーブルの入力
def write_project(pname,nsprint,stats):
    try:
        connector = psycopg2.connect(
            'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
                user="postgres",       
                password="selab",     
                host="172.21.40.30",   
                port="5432",          
                dbname="QDT-DB",
                )
            )      
        cursor = connector.cursor()
        check_query = "SELECT pid FROM project WHERE pname = %s"
        cursor.execute(check_query, (pname,))
        existing_pid = cursor.fetchone()
        if existing_pid:
            check_rmax = "SELECT MAX(cid) FROM qualitynode WHERE pid = %s"
            cursor.execute(check_rmax, (existing_pid[0],))
            existing_rmax = cursor.fetchone()
            if existing_rmax[0]==None:
                rmax=0
            else:
                rmax=existing_rmax[0]
            update_project = "UPDATE project SET rmax = %s,nsprint = %s ,status=%s WHERE pid = %s;"
            cursor.execute(update_project, (rmax, nsprint,stats,existing_pid[0],))
            connector.commit()  
        else:
            insert_query = "INSERT INTO project (pname, rmax, nsprint, status) VALUES (%s, %s, %s, %s)"
            record_to_insert = (pname, 0, nsprint, stats)
            cursor.execute(insert_query, record_to_insert)
            connector.commit()  
            
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return None

#ノードの書き込み
def write_node(pid,node_name,type,subtype,content,contribution,destination,child_nid=None):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()
        #nid検索
        check_contribution = """
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_contribution, (node_name,pid))
        nid = cursor.fetchone()
        #同じノードがある場合
        if nid != None:
            update_query = "UPDATE qualitynode SET content = %s  WHERE nid = %s;"
            cursor.execute(update_query, (json.dumps(content), nid[0],))
            connector.commit()  # 変更をコミット
            #sidの検索
            check_contribution = """
                            SELECT sid
                            FROM support
                            WHERE source = %s;
                        """
            cursor.execute(check_contribution, (nid))
            sid = cursor.fetchone()
            update_query1 = "UPDATE support SET destination = %s,contribution = %s WHERE sid = %s;"
            cursor.execute(update_query1, (destination, contribution,sid[0],))
            connector.commit()  # 変更をコミット
            print('更新終了')
        
        #同じノードがない場合
        else:
            qu = "SELECT COUNT(*) FROM qualitynode WHERE type LIKE %s AND pid = %s;"
            cursor.execute(qu, ('%' + type + '%',pid))
            row_count = cursor.fetchone()
            if row_count[0] is not None:
                cid_value = row_count[0] + 1
            else:
                cid_value=1
            insert_query = "INSERT INTO qualitynode (pid, cid, type, subtype, content) VALUES (%s, %s, %s, %s, %s)"
            record_to_insert = (pid, cid_value, type, subtype, json.dumps(content))
            cursor.execute(insert_query, record_to_insert)
            connector.commit()
            #nidの検索
            check_contribution = """
                            SELECT nid
                            FROM qualitynode
                            WHERE content ->> 'subchar' = %s AND pid = %s;
                        """
            cursor.execute(check_contribution, (node_name,pid))
            nid = cursor.fetchone()
            #support書き込み
            insert_query1 = "INSERT INTO support (source, destination, contribution) VALUES (%s, %s, %s)"
            record_to_insert1 = (nid[0], destination, contribution)
            cursor.execute(insert_query1, record_to_insert1)
            if child_nid:
                update_query2 = "UPDATE support SET destination = %s WHERE source = %s;"
                cursor.execute(update_query2, (nid[0], child_nid,))
            connector.commit()  
            print('更新終わり')
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return None

#ノードの確認
def check_nid(pname,node):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()
        #プロジェクトidの確認
        check_pid = "SELECT pid FROM project WHERE pname = %s"
        cursor.execute(check_pid, (pname,))
        existing_pid = cursor.fetchone()
        pid=existing_pid[0]
        
        #ノードがあるかどうか検索
        check_aim = """
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_aim, (node,pid,))
        aim_value = cursor.fetchone()
        if aim_value:
            message=aim_value[0]
        else:
            message='none'
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message

#ノード＋説明の確認
def check_node(pname,node):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()
        #プロジェクトidの確認
        check_pid = "SELECT pid FROM project WHERE pname = %s"
        cursor.execute(check_pid, (pname,))
        existing_pid = cursor.fetchone()
        pid=existing_pid[0]
        
        #ノードがあるかどうか検索
        check_aim = """
                        SELECT nid,content ->> 'statement' as statement
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_aim, (node,pid,))
        aim_value = cursor.fetchone()
        if aim_value:
            message=aim_value
        else:
            message='none'
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message

#子のリストを作る
def make_child(nid):
    aim_value=[]
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()
        #子を探す
        child = """
                        SELECT qualitynode.type,qualitynode.content,support.contribution
                        FROM qualitynode
                        JOIN support ON qualitynode.nid=support.source
                        WHERE destination=%s;
                    """
        cursor.execute(child, (nid,))
        aim_value = cursor.fetchall()
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return aim_value

#名前をとる
def check_name(nid,pid):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()
        #子を探す
        check_aim = """
                        SELECT content ->> 'subchar' as subchar_value
                        FROM qualitynode
                        WHERE nid = %s AND pid = %s;
                    """
        cursor.execute(check_aim, (nid,pid,))
        subchar_value = cursor.fetchone()
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return subchar_value[0]

#typeをとる
def check_type(name):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()
        #子を探す
        check_aim = """
                        SELECT type
                        FROM qualitynode
                        WHERE  content ->> 'subchar' = %s ;
                    """
        cursor.execute(check_aim, (name,))
        type = cursor.fetchone()
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return type[0]

#supportテーブル　貢献度の確認
def check_contribution(pid,node):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()      
        #貢献度があるかどうか検索
        check_contribution = """
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_contribution, (node,pid,))
        nid = cursor.fetchone()
        if nid:
            check_pid = "SELECT contribution FROM support WHERE source = %s"
            cursor.execute(check_pid, (nid[0],))
            existing_contribution = cursor.fetchone()
            contribution=existing_contribution[0]
            message=contribution
        else:
            message=0
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message

#qualitynodeテーブル　手法の確認
def check_description(pid,node):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()
        #手法記載があるかどうか検索
        check_aim = """
                        SELECT content ->> 'description' as description_value
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_aim, (node,pid,))
        description_value = cursor.fetchone()
        if description_value:
            message=description_value[0]
        else:
            message=None
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message

#qualitynodeテーブル　目標値の確認
def check_scope(pid,node):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()        
        #許容範囲があるかどうか検索
        check_aim = """
                        SELECT content ->> 'tolerance' as tolerance_value
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_aim, (node,pid,))
        scape_value = cursor.fetchone()
        if scape_value:
            message=eval(scape_value[0])
        else:
            message=[0.70,0.85]
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message

#qualitynodeテーブル　達成度
def check_achievement(pid,node):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor()        
        #達成度があるかどうか検索
        check_aim = """
                        SELECT achievement
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_aim, (node,pid,))
        scape_value = cursor.fetchone()
        if scape_value[0]!=None:
            message=scape_value[0]
        else:
            message=0.0
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return round(message)

#qualitynodeテーブル　前の達成度
def check_achievement_old(pid,node):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        
        cursor = connector.cursor() 
        check_contribution = """
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_contribution, (node,pid,))
        nid = cursor.fetchone()
        if nid[0]!=None:       
            #logがあるかどうか検索
            check_aim = """
                            SELECT achievement
                            FROM log
                            WHERE nid = %s
                            ORDER BY lid DESC 
                            LIMIT 1;
                        """
            cursor.execute(check_aim, (nid[0],))
            scape_value = cursor.fetchone()
            if scape_value==None:
                message=0.0
            else:
                message=scape_value[0]
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return round(message)