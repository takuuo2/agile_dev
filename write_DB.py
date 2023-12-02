import psycopg2
from psycopg2 import Error
import json

#projectテーブルの入力と確認
def w_project(pname):
    try:
        # PostgreSQLに接続
        connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user="postgres",        # ユーザ名
        password="selab",      # パスワード
        host="172.21.40.30",   # ホスト名
        port="5432",           # ポート番号
        dbname="QDT-DB"))      # データベース名
        cursor = connector.cursor()
        check_query = "SELECT pid FROM project WHERE pname = %s"
        cursor.execute(check_query, (pname,))
        existing_pid = cursor.fetchone()
        if existing_pid:
            #print(f"同じプロジェクト名が存在します: {existing_pid[0]}")
            message=existing_pid[0]
        else:
            insert_query = "INSERT INTO project (pname, rmax, nsprint, status) VALUES (%s, %s, %s, %s)"
            record_to_insert = (pname, '0', '0', 'planning')
            cursor.execute(insert_query, record_to_insert)
            connector.commit()  
            check_query = "SELECT pid FROM project WHERE pname = %s"
            cursor.execute(check_query, (pname,))
            existing_pid = cursor.fetchone()
            message=existing_pid[0]
            
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message

#qualitynodeテーブル　目標値の確認
def check_aim(pname,node):
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
        
        #目標値があるかどうか検索
        check_aim = """
                        SELECT content ->> 'aim' as aim_value
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_aim, (node,pid,))
        aim_value = cursor.fetchone()
        if aim_value:
            message=aim_value[0]
        else:
            message=0.0
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message

#supportテーブル　貢献度の確認
def check_contribution(pname,node):
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
        
        #目標値があるかどうか検索
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
            if contribution==3:
                message='H'
            elif contribution==2:
                message='M'
            elif contribution==1:
                message='L'
            else:
                message='N'
        else:
            message='N'
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return message


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
        
        #目標値があるかどうか検索
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
        check_aim = """
                        SELECT source
                        FROM support
                        WHERE destination=%s;
                    """
        cursor.execute(check_aim, (nid,))
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

#ノードの書き込み
def write_node(pname,node,type,subtype,aim,contribution,destination):
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
        
        #タイプで変更
        if type=='REQ':
            text={'subchar':node}
        elif type=='IMP':
            text={'subchar':node}
        else:
            text={'subchar':node,'aim':aim}
         
        #nid検索
        check_contribution = """
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    """
        cursor.execute(check_contribution, (node,pid))
        nid = cursor.fetchone()
        #同じノードがある場合
        if nid != None:
            update_query = "UPDATE qualitynode SET content = %s WHERE nid = %s;"
            cursor.execute(update_query, (json.dumps(text), nid[0],))
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
            qu = "SELECT COUNT(*) FROM qualitynode WHERE type LIKE %s;"
            cursor.execute(qu, ('%' + type + '%',))
            row_count = cursor.fetchone()
            if row_count[0] is not None:
                cid_value = row_count[0] + 1
            else:
                cid_value=1
            insert_query = "INSERT INTO qualitynode (pid, cid, type, subtype, content) VALUES (%s, %s, %s, %s, %s)"
            record_to_insert = (pid, cid_value, type, subtype, json.dumps(text),)
            cursor.execute(insert_query, record_to_insert)
            connector.commit()
            #nidの検索
            check_contribution = """
                            SELECT nid
                            FROM qualitynode
                            WHERE content ->> 'subchar' = %s AND pid = %s;
                        """
            cursor.execute(check_contribution, (node,pid))
            nid = cursor.fetchone()
            #support書き込み
            insert_query1 = "INSERT INTO support (source, destination, contribution) VALUES (%s, %s, %s)"
            record_to_insert1 = (nid[0], destination, contribution)
            cursor.execute(insert_query1, record_to_insert1)
            connector.commit()  
            print('更新終わり')
        
    except (Exception, Error) as error:
        print("PostgreSQLへの接続時のエラーが発生しました:", error)

    finally:
        cursor.close()
        connector.close()
    return None


