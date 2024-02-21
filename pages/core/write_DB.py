import psycopg2
from psycopg2 import Error
import json


#確認
def check_db(select,node):
  try:
    connector = psycopg2.connect(
      'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user='postgres',        
        password='selab',  
        host='172.21.40.30',  
        port='5432',           
        dbname='QDT-DB'
        )
      )      
    cursor = connector.cursor()
    cursor.execute(select, (node,))
    existing_pid = cursor.fetchone()
    if existing_pid:
      message=existing_pid
    else:
      message='none'
  except (Exception, Error) as error:
    print('接続時のエラーが発生しました:', error)
  finally:
    cursor.close()
  return message

#project書き込み
def write_project(pname,nsprint,stats):
  try:
    connector = psycopg2.connect(
      'postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
        user='postgres',       
        password='selab',    
        host='172.21.40.30',   
        port='5432',          
        dbname='QDT-DB',
        )
      )      
    cursor = connector.cursor()
    check_query = 'SELECT pid FROM project WHERE pname = %s'
    cursor.execute(check_query, (pname,))
    existing_pid = cursor.fetchone()
    if existing_pid:
      check_rmax = 'SELECT MAX(cid) FROM qualitynode WHERE pid = %s'
      cursor.execute(check_rmax, (existing_pid[0],))
      existing_rmax = cursor.fetchone()
      if existing_rmax == None:
        rmax = 0
      else:
        rmax = existing_rmax[0]
        update_project = 'UPDATE project SET rmax = %s,nsprint = %s ,status=%s WHERE pid = %s;'
        cursor.execute(update_project, (rmax, nsprint,stats,existing_pid[0],))
        connector.commit()  
    else:
      insert_query = 'INSERT INTO project (pname, rmax, nsprint, status) VALUES (%s, %s, %s, %s)'
      record_to_insert = (pname, 0, nsprint, stats,)
      cursor.execute(insert_query, record_to_insert)
      connector.commit()     
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
    cursor.close()
    connector.close()
  return None

#ノードの書き込み
def write_node(pid,node_name,type,subtype,content,contribution,destination,achievement,child_nid=None):
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
      user='postgres',        
      password='selab',     
      host='172.21.40.30',   
      port='5432',          
      dbname='QDT-DB'))   
    cursor = connector.cursor()
    #nid検索
    check_contribution = '''
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    '''
    cursor.execute(check_contribution, (node_name,pid))
    nid = cursor.fetchone()
    #同じノードがある場合
    if nid != None:
      print('onaji')
      update_query = 'UPDATE qualitynode SET content = %s  WHERE nid = %s;'
      cursor.execute(update_query, (json.dumps(content), nid[0],))
      connector.commit()  
      #sidの検索
      check_contribution = '''
                      SELECT sid
                      FROM support
                      WHERE source = %s;
                  '''
      cursor.execute(check_contribution, (nid[0],))
      sid = cursor.fetchone()
      update_query1 = 'UPDATE support SET destination = %s,contribution = %s WHERE sid = %s;'
      cursor.execute(update_query1, (destination, contribution,sid[0],))
      connector.commit()  
      print('更新終了')
        
    #同じノードがない場合
    else:
      qu = 'SELECT COUNT(*) FROM qualitynode WHERE type LIKE %s AND pid = %s;'
      cursor.execute(qu, ('%' + type + '%',pid,))
      row_count = cursor.fetchone()
      if row_count[0] != 0:
        cid_value = row_count[0] + 1
      else:
        cid_value=1
      insert_query = 'INSERT INTO qualitynode (pid, cid, type, subtype, content, achievement) VALUES (%s, %s, %s, %s, %s, %s)'
      record_to_insert = (pid, cid_value, type, subtype, json.dumps(content),achievement,)
      cursor.execute(insert_query, record_to_insert)
      connector.commit()
      #nidの検索
      check_contribution = '''
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    '''
      cursor.execute(check_contribution, (node_name,pid))
      nid = cursor.fetchone()
      #support書き込み
      insert_query1 = 'INSERT INTO support (source, destination, contribution) VALUES (%s, %s, %s)'
      record_to_insert1 = (nid[0], destination, contribution)
      cursor.execute(insert_query1, record_to_insert1)
      if child_nid:
          update_query2 = 'UPDATE support SET destination = %s WHERE source = %s;'
          cursor.execute(update_query2, (nid[0], child_nid,))
      connector.commit()  
      print('更新終わり')
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()
  return None

#ノードの確認
def check_node(pid,node):
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
      user='postgres',        
      password='selab',     
      host='172.21.40.30',   
      port='5432',        
      dbname='QDT-DB'))     
    cursor = connector.cursor()
    check_aim = ''' SELECT * FROM qualitynode
                    WHERE content ->> 'subchar' = %s AND pid = %s;
                '''
    cursor.execute(check_aim, (node,pid,))
    aim_value = cursor.fetchone()
    if aim_value:
      message=aim_value
    else:
      message='none'
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
    cursor.close()
    connector.close()
  return message


#子のリストを作る
def make_child(nid):
  aim_value=[]
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
      user='postgres',      
      password='selab',     
      host='172.21.40.30',   
      port='5432',           
      dbname='QDT-DB'))      
    cursor = connector.cursor()
    child = '''
      SELECT qualitynode.type,qualitynode.content,support.contribution
      FROM qualitynode
      JOIN support ON qualitynode.nid=support.source
      WHERE destination=%s;
      '''
    cursor.execute(child, (nid,))
    aim_value = cursor.fetchall()
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
      cursor.close()
      connector.close()
  return aim_value

#qualitynodeテーブル　前の達成度
def check_achievement_old(pid,node):
  try:
    # PostgreSQLに接続
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    user='postgres',        
    password='selab',
    host='172.21.40.30',   
    port='5432',           
    dbname='QDT-DB'))      
    cursor = connector.cursor() 
    check_contribution = '''
                        SELECT nid
                        FROM qualitynode
                        WHERE content ->> 'subchar' = %s AND pid = %s;
                    '''
    cursor.execute(check_contribution, (node,pid,))
    nid = cursor.fetchone()
    if nid!=None:   
      check_aim = '''
                  SELECT achievement
                  FROM log
                  WHERE nid = %s
                  ORDER BY lid DESC 
                  LIMIT 1;
              '''
      cursor.execute(check_aim, (nid[0],))
      scape_value = cursor.fetchone()
      if scape_value==None:
          message=0.0
      else:
          message=scape_value[0]
        
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()
  return round(message)


#qualitynodeテーブル　手法の確認
def check_description(pid,node):
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
      user='postgres',        
      password='selab',     
      host='172.21.40.30',  
      port='5432',         
      dbname='QDT-DB'))    
    cursor = connector.cursor()
    check_aim = '''
                  SELECT content ->> 'description' as description_value
                  FROM qualitynode
                  WHERE content ->> 'subchar' = %s AND pid = %s;
              '''
    cursor.execute(check_aim, (node,pid,))
    description_value = cursor.fetchone()
    if description_value:
      message=description_value[0]
    else:
      message=None
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
      cursor.close()
      connector.close()
  return message

#supportテーブル　貢献度の確認
def check_contribution(pid,node):
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
      user='postgres',       
      password='selab',      
      host='172.21.40.30',  
      port='5432',         
      dbname='QDT-DB'))    
    cursor = connector.cursor()      
    check_contribution = '''
              SELECT nid
              FROM qualitynode
              WHERE content ->> 'subchar' = %s AND pid = %s;
          '''
    cursor.execute(check_contribution, (node,pid,))
    nid = cursor.fetchone()
    if nid:
      check_pid = 'SELECT contribution FROM support WHERE source = %s'
      cursor.execute(check_pid, (nid[0],))
      existing_contribution = cursor.fetchone()
      message=existing_contribution[0]
    else:
      message=0
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
      cursor.close()
      connector.close()
  return message

#qualitynodeテーブル　目標値の確認
def check_scope(pid,node):
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    user='postgres',      
    password='selab',      
    host='172.21.40.30',  
    port='5432',          
    dbname='QDT-DB'))             
    cursor = connector.cursor()        
    check_aim = '''
              SELECT content ->> 'tolerance' as tolerance_value
              FROM qualitynode
              WHERE content ->> 'subchar' = %s AND pid = %s;
          '''
    cursor.execute(check_aim, (node,pid,))
    scape_value = cursor.fetchone()
    if scape_value:
      message=eval(scape_value[0])
    else:
      message=[0.70,0.85]    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
    cursor.close()
    connector.close()
  return message


#projectテーブル
def read_table(request,pid=None):
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    user='postgres',      
    password='selab',      
    host='172.21.40.30',  
    port='5432',          
    dbname='QDT-DB'))             
    cursor = connector.cursor()
    if pid == None:
      cursor.execute(request)
    else:
      cursor.execute(request, (pid,))
    data = cursor.fetchall()
    if data:
      message=data
    else:
      message='none'    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
    cursor.close()
    connector.close()
  return message

#ルートの確認
def getRoots(pid):
  try:
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    user='postgres',      
    password='selab',      
    host='172.21.40.30',  
    port='5432',          
    dbname='QDT-DB'))             
    cursor = connector.cursor()
    check_aim = '''
                 SELECT q.content, q.achievement,s.contribution,q.nid
                 FROM qualitynode q
                 JOIN support s ON q.nid = s.source
                 WHERE s.destination = '0' AND q.pid = %s;
              '''
    cursor.execute(check_aim, (pid,))
    data = cursor.fetchall()
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)
  finally:
    cursor.close()
    connector.close()
  return data


#qualitynodeテーブル 達成度
def achievement(nid,sprint):
  try:
    # PostgreSQLに接続
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    user='postgres',        
    password='selab',
    host='172.21.40.30',   
    port='5432',           
    dbname='QDT-DB'))      
    cursor = connector.cursor() 
    check_aim = '''
        SELECT achievement
        FROM log
        WHERE nid = %s AND sprint = %s;
        '''
    cursor.execute(check_aim, (nid,sprint,))
    scape_value = cursor.fetchone()
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()
  return scape_value

#ノードの取り出し
def get_nodes(pid):
  try:
    # PostgreSQLに接続
    connector = psycopg2.connect('postgresql://{user}:{password}@{host}:{port}/{dbname}'.format(
    user='postgres',        
    password='selab',
    host='172.21.40.30',   
    port='5432',           
    dbname='QDT-DB'))      
    cursor = connector.cursor() 
    check_aim = '''
        SELECT *
        FROM qualitynode
        WHERE pid = %s ;
        '''
    cursor.execute(check_aim, (pid,))
    scape_value = cursor.fetchall()
    
  except (Exception, Error) as error:
    print('PostgreSQLへの接続時のエラーが発生しました:', error)

  finally:
    cursor.close()
    connector.close()
  return scape_value
