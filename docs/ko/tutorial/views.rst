.. _tutorial-views:

스텝 5: 뷰 함수들
==========================

이제 데이터베이스 연결이 제대로 작동하므로 우리는 이제 뷰함수 작성을
시작할 수 있다. 우리는 뷰함수중 네가지를 사용합니다.


작성된 글 보여주기
------------

이뷰는 데이터베이스에 저장된 모든 글들을 보여준다. 
이뷰에서는 어플리케이션 루트에서 대기하고 있다가 요청이 오면 데이터베이스의 
title 컬럼과 text 컬럼에서 자료를 검색하여 보여준다.
가장 큰 값을 가지고 있는 id (가장 최신 항목)를 제일 위에서 보여준다.
커서를 통해 리턴되는 row들은 select 구문에서 명시된 순서대로 정리된 튜플(tuples)이다. 
여기에서 다루는 예에서 사용하는 작은 어플리케이션에게는 이정도 기능만으로도
충분하다. 하지만 튜플들을 dict타입으로 변경하고 싶을수도 있을것이다. 
만약 어떻게 변경이 가능한지 흥미있다면 다음의 예제를 참고 할 수 있다.
:ref:`easy-querying` 예제.

뷰 함수는 데이터베이스에서 검색된 항목들을 dict 타입으로 `show_entries.html` template 에 
렌더링하여 리턴한다. ::

    @app.route('/')
    def show_entries():
        cur = g.db.execute('select title, text from entries order by id desc')
        entries = [dict(title=row[0], text=row[1]) for row in cur.fetchall()]
        return render_template('show_entries.html', entries=entries)

새로운 글 추가하기
-------------

이뷰는 로그인한 사용자에게 새로운 글을 작성하게 해준다. 이뷰는 오직
`POST` 리퀘스트에만 응답하도록 하고 이와 관련된 실제 form은 `show_entries` 
페이지에 있다. 만약 모든것이 제대로 작동하고 있다면 :func:`~flask.flash`  에서 
메시지로 새로작성된 글에 대한 정보를 보여주고 `show_entries` 페이지로 리다이렉션한다.::


    @app.route('/add', methods=['POST'])
    def add_entry():
        if not session.get('logged_in'):
            abort(401)
        g.db.execute('insert into entries (title, text) values (?, ?)',
                     [request.form['title'], request.form['text']])
        g.db.commit()
        flash('New entry was successfully posted')
        return redirect(url_for('show_entries'))

우리는 여기에서 사용자가 로그인되었는지 체크 할 것이라는 것을 주목하자.
(세션에서  `logged_in` 키가 존재하고 값이 `True` 인지 확인한다.)

.. admonition:: Security Note

   위의 예에서 SQL 구문을 생성할때 물음표를 사용하도록 해야 한다.
   그렇지 않고 SQL 구문에서 문자열 포맷팅을 사용하게 되면 당신의 
   어플리케이션은 SQL injection에 취약해질 것이다.
   다음의 섹션을 확인해보자:ref:`sqlite3` 

로그인과 로그아웃
----------------

이 함수들은 사용자의 로그인과 로그아웃에 사용된다. 로그인을 할때에는
입력받은 사용자이름과 패스워드를 설정에서 셋팅한 값과 비교하여 
세션의 `logged_in` 키에 값을 설정하여 로그인상태와 로드아웃상태를 결정한다.
만약 사용자가 성공적으로 로그인 되었다면 키값에 `True` 를 셋팅한 후에 `show_entries` 
페이지로 리다이렉트한다.

또한 사용자가 성공적으로 로그인되었는지 메시지로 정보를 보여준다.
만약 오류가 발생하였다면, 템플릿에서 오류내용에 대해 통지하고 사용자에게 
다시 질문하도록 한다.::


    @app.route('/login', methods=['GET', 'POST'])
    def login():
        error = None
        if request.method == 'POST':
            if request.form['username'] != app.config['USERNAME']:
                error = 'Invalid username'
            elif request.form['password'] != app.config['PASSWORD']:
                error = 'Invalid password'
            else:
                session['logged_in'] = True
                flash('You were logged in')
                return redirect(url_for('show_entries'))
        return render_template('login.html', error=error)


다른 한편으로 로그아웃 함수는 세션에서 `logged_in` 키값에 대하여 로그인 설정에
대한 값을 제거한다. 우리는 여기에서 정교한 트릭을 사용할 것이다 : 만약 당신이 dict객체의 
:meth:`~dict.pop` 함수에 두번째 파라미터(기본값)를 전달하여 사용하면 이 함수는 만약 해당 키가 
dcit객체에 존재하거나 그렇지 않은 경우 dict객체에서 해당 키를 삭제할 것이다. 
이 방법은 사용자가 로그인 하였는지 아닌지 체크할 필요가 없기 때문에 유용하다.

::

    @app.route('/logout')
    def logout():
        session.pop('logged_in', None)
        flash('You were logged out')
        return redirect(url_for('show_entries'))

다음 섹션에 계속된다.  :ref:`tutorial-templates`.
