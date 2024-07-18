from flask import Flask, g
from flask import render_template, request, redirect, url_for
import sqlite3
import unicodedata


app = Flask(__name__)

DATABASE: str = 'sample.db'

# 処理結果コードとメッセージ
RESULT_MESSAGES: dict[str, str] = {
    'book-id-has-invalid-charactor':
    '指定された本番号には使えない文字があります - '
    '数字のみで指定してください',
    'book-id-does-not-exist':
    '指定された本番号は存在しません - ',
    'book-id-already-exists':
    '指定された本番号は既に存在します - '
    '存在しない本番号を指定してください',
    'copy-id-has-invalid-charactor':
    '指定された蔵書IDには使えない文字があります - ',
    'copy-already-exists':
    '指定された蔵書IDは既に存在します - ',
    'copy-id-does-not-exist':
    '指定された蔵書IDは存在しません - ',
    'library-id-has-invalid-charactor':
    '指定された図書館IDには使えない文字があります - ',
    'library-id-does-not-exists':
    '指定された図書館IDは存在しません - ',
    'book-is-in-library':
    '指定された本の蔵書が存在します - '
    '蔵書を先に削除してください',
    'publish-year-has-invalid-charactor':
    '指定された出版年には使えない文字があります - '
    '数字のみで指定してください',
    'birth-year-has-invalid-charactor':
    '指定された生年には使えない文字があります - '
    '数字のみで指定してください',
    'genre-id-has-invalid-charactor':
    '指定されたジャンルIDには使えない文字があります - '
    '数字のみで指定してください',
    'genre-id-does-not-exists':
    '指定されたジャンルIDは存在しません - ',
    'title-has-control-charactor':
    '指定されたタイトルには制御文字があります - '
    '制御文字は指定しないでください',
    'author-id-has-invalid-charactor':
    '指定された著者IDには使えない文字があります - '
    '数字のみで指定してください',
    'user-id-has-invalid-charactor':
    '指定されたユーザーIDには使えない文字があります - '
    '数字のみで指定してください',
    'user-id-already-exists':
    '指定されたユーザーIDは既に存在します - '
    '存在しないユーザーIDを指定してください',
    'name-has-control-charactor':
    '指定された名前には制御文字があります - '
    '制御文字は指定しないでください',
    'email-address-has-control-charactor':
    '指定されたメールアドレスには制御文字があります - '
    '制御文字は指定しないでください',
    'phone-number-has-control-charactor':
    '指定された携帯電話番号には制御文字があります - '
    '制御文字は指定しないでください',
    'borrow-time-has-control-charactor':
    '貸し出し日に制御文字があります。制御文字は使用しないでください',
    'return-time-has-control-charactor':
    '返却日に制御文字があります。制御文字は使用しないでください',
    'database-error':
    'データベースエラー',
    'book-added':
    '本を追加しました',
    'copy-added':
    '蔵書を追加しました',
    'user-added':
    'ユーザーを追加しました',
    'borrow-added':
    '貸し出しが完了しました。',
    'return-added':
    '返却が完了しました。',
    'history-deleted':
    '貸し出し履歴を削除しました',
    'deleted':
    '削除しました',
    'user-deleted':
    'ユーザーを削除しました',
    'updated':
    '更新しました'
}


def get_db() -> sqlite3.Connection:
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row  # カラム名でアクセスできるよう設定変更
    return db


@app.teardown_appcontext
def close_connection(exception) -> None:
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def has_control_character(s: str) -> bool:
    return any(map(lambda c: unicodedata.category(c) == 'Cc', s))


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/books')
def books() -> str:
    cur = get_db().cursor()
    # 図書館が所有する全ての本のタイトルの情報を取得
    coordinates = 'SELECT  B.BookID, b.Title, b.Year, b.genreID, Genre.Name FROM Books b    ' \
                  'JOIN Genre ON b.GenreID = Genre.GenreID;'
    e_list = cur.execute(coordinates).fetchall()
    return render_template('books.html', e_list=e_list)


@app.route('/books_filtered', methods=['POST'])
def books_filtered() -> str:
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # Books テーブルからタイトルで絞り込み、
    e_list = cur.execute('SELECT  B.BookID, b.Title, b.Year, b.genreID, Genre.Name FROM Books b '
                         'JOIN Genre ON b.GenreID = Genre.GenreID WHERE Title LIKE ?;',
                         (request.form['title_filter'], )).fetchall()

    # 一覧をテンプレートへ渡してレンダリングしたものを返す
    return render_template('books.html', e_list=e_list)


@app.route('/genres_filtered', methods=['POST'])
def genres_filtered() -> str:
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # Users テーブルから名前で絞り込み、
    e_list = cur.execute('SELECT  B.BookID, b.Title, b.Year, b.genreID, Genre.Name FROM Books b '
                         'JOIN Genre ON b.GenreID = Genre.GenreID WHERE Genre.GenreID LIKE ?;',
                         (request.form['genre_filter'], )).fetchall()
    # 一覧をテンプレートへ渡してレンダリングしたものを返す
    return render_template('books.html', e_list=e_list)


@app.route('/books/<id>')
def book(id: str) -> str:
    con = get_db()
    cur = con.cursor()

    try:
        id_num = int(id)
    except ValueError:  # id が数値でない場合
        return render_template('book-not-found.html')

    coordinate_book = '''
    SELECT
    Books.BookID,
    Books.Title,
    Books.Year,
    Genre.Name,
    Genre.GenreID
    FROM
        Books
    JOIN
        Genre ON Books.GenreID = Genre.GenreID
    WHERE
        Books.BookID = ?;
    '''

    coordinate_library = '''
    SELECT l.Name, c.copyID
    FROM Copies c
    JOIN Books b ON c.BookID = b.BookID
    JOIN Libraries l ON c.LibraryID = l.LibraryID
    WHERE b.BookID = ?;
    '''

    coordinate_author = '''
    SELECT
    Authors.Name
    FROM
        Books
    JOIN
        CoAuthors ON Books.BookID = CoAuthors.BookID
    JOIN
        Authors ON CoAuthors.AuthorID = Authors.AuthorID
    WHERE
        Books.BookID = ?;
    '''

    book = cur.execute(coordinate_book, (id_num, )).fetchone()
    libraries = cur.execute(coordinate_library, (id_num, )).fetchall()
    authors = cur.execute(coordinate_author, (id_num, )).fetchall()

    if book is None:  # 本が見つからなかった場合
        return render_template('book-not-found.html')

    return render_template('book.html', book=book, libraries=libraries, authors=authors)


@app.route('/book-add')
def book_add() -> str:
    # テンプレートへ何も渡さずにレンダリングしたものを返す
    return render_template('book-add.html')


@app.route('/book-add', methods=['POST'])
def book_add_execute():
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # リクエストされた POST パラメータの内容を取り出す
    book_id_str = request.form['book_id']
    title = request.form['title']
    publish_year_str = request.form['publish_year']
    multi_author = request.form['author_id']
    genre_id_str = request.form['genre_id']

    # 本番号チェック
    try:
        book_id = int(book_id_str)  # 文字列型で渡された本番号を整数型へ変換する
    except ValueError:
        # 本番号が整数型へ変換できない
        return redirect(url_for('book_add_results',
                                code='book-id-has-invalid-charactor'))
    # 本番号の存在チェックをする：
    # books テーブルで同じ本番号の行を 1 行だけ取り出す
    book = cur.execute('SELECT BookID FROM Books WHERE BookID = ?',
                           (book_id,)).fetchone()
    if book is not None:
        # 指定された本番号の行が既に存在
        return redirect(url_for('book_add_results',
                                code='book-id-already-exists'))

    # タイトルチェック
    if has_control_character(title):
        # 名前に制御文字が含まれる
        return redirect(url_for('book_add_results',
                                code='title-has-control-charactor'))

    # 出版年チェック
    try:
        # 文字列型で渡された出版年を整数型へ変換する
        publish_year = int(publish_year_str)
    except ValueError:
        # 出版年が整数型へ変換できない
        return redirect(url_for('book_add_results',
                                code='publish-year-has-invalid-charactor'))

    # ジャンルIDチェック
    try:
        # 文字列型で渡された出版年を整数型へ変換する
        genre_id = int(genre_id_str)
    except ValueError:
        # 出版年が整数型へ変換できない
        return redirect(url_for('book_add_results',
                                code='genre-id-has-invalid-charactor'))
    # ジャンル番号の存在チェックをする：
    # Genre テーブルで同じ本番号の行を 1 行だけ取り出す
    genre = cur.execute('SELECT GenreID FROM Genre WHERE GenreID = ?',
                           (genre_id,)).fetchone()
    if genre is None:
        # 指定された本番号の行が既に存在
        return redirect(url_for('book_add_results',
                                code='genre-id-does-not-exists'))

    # 著者チェック
    authors = multi_author.split(',')
    for author in authors:
        try:
            int(author)
        except ValueError:
            return redirect(url_for('book_add_results',
                                    code='author-id-has-invalid-charactor'))

    # データベースへ本を追加
    try:
        # Books テーブルに指定されたパラメータの行を挿入
        cur.execute('INSERT INTO Books '
                    '(BookID, Title, Year, GenreID) '
                    'VALUES (?, ?, ?, ?)',
                    (book_id, title, publish_year, genre_id))
    except sqlite3.Error:
        # データベースエラーが発生
        return redirect(url_for('book_add_results',
                                code='database-error'))
    for author in authors:
        # データベースへ本の筆者を追加
        author = int(author)
        try:
            # CoAuthors テーブルに指定されたパラメータの行を挿入
            cur.execute('INSERT INTO CoAuthors'
                        '(BookID, AuthorID) '
                        'VALUES (?, ?)',
                        (book_id, author))
        except sqlite3.Error:
            # データベースエラーが発生
            return redirect(url_for('book_add_results',
                                    code='database-error'))
    # コミット（データベース更新処理を確定）
    con.commit()

    # 本追加完了
    return redirect(url_for('book_add_results',
                            code='book-added'))


@app.route('/book-add-results/<code>')
def book_add_results(code: str) -> str:
    return render_template('book-add-results.html',
                           # codeが存在しなければ'code error 'を返す
                           results=RESULT_MESSAGES.get(code, 'code error')
                           )


@app.route('/copy-add')
def copy_add() -> str:
    # テンプレートへ何も渡さずにレンダリングしたものを返す
    return render_template('copy-add.html')


@app.route('/copy-add', methods=['POST'])
def copy_add_execute():
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # リクエストされた POST パラメータの内容を取り出す
    book_id_str = request.form['book_id']
    copy_id_str = request.form['copy_id']
    library_id_str = request.form['library_id']

    # 本番号チェック
    try:
        book_id = int(book_id_str)  # 文字列型で渡された本番号を整数型へ変換する
    except ValueError:
        # 本番号が整数型へ変換できない
        return redirect(url_for('copy_add_results',
                                code='book-id-has-invalid-charactor'))
    # 本番号の存在チェックをする：
    # books テーブルで同じ本番号の行を 1 行だけ取り出す
    book = cur.execute('SELECT BookID FROM Books WHERE BookID = ?',
                           (book_id,)).fetchone()
    if book is None:
        # 指定された本番号の行が存在しない場合
        return redirect(url_for('copy_add_results',
                                code='book-id-does-not-exist'))

    # copyIDチェック
    try:
        # 文字列型で渡された蔵書idを整数型へ変換する
        copy_id = int(copy_id_str)
    except ValueError:
        # 出版年が整数型へ変換できない
        return redirect(url_for('copy_add_results',
                                code='copy-id-has-invalid-charactor'))
    # Copy番号の存在チェックをする：
    # Copyテーブルで同じ本番号の行を 1 行だけ取り出す
    copy = cur.execute('SELECT CopyID FROM Copies WHERE CopyID = ?',
                           (copy_id,)).fetchone()
    if copy is not None:
        # 指定された蔵書番号の行が既に存在
        return redirect(url_for('copy_add_results',
                                code='copy-already-exists'))

    # 図書館番号チェック
    try:
        library_id = int(library_id_str)  # 文字列型で渡された図書館番号を整数型へ変換する
    except ValueError:
        # 図書館番号が整数型へ変換できない
        return redirect(url_for('copy_add_results',
                                code='library-id-has-invalid-charactor'))
    # 図書館番号の存在チェックをする：
    # Librariesテーブルで同じ図書館番号の行を 1 行だけ取り出す
    library = cur.execute('SELECT LibraryID FROM Libraries WHERE LibraryID = ?',
                           (library_id,)).fetchone()
    if library is None:
        # 指定された図書館番号の行が存在しない場合
        return redirect(url_for('copy_add_results',
                                code='library-id-does-not-exists'))

    # データベースへ本を追加
    try:
        # Books テーブルに指定されたパラメータの行を挿入
        cur.execute('INSERT INTO Copies '
                    '(CopyID, BookID, LibraryID) '
                    'VALUES (?, ?, ?)',
                    (copy_id, book_id, library_id))
    except sqlite3.Error:
        # データベースエラーが発生
        return redirect(url_for('copy_add_results',
                                code='database-error'))
    # コミット（データベース更新処理を確定）
    con.commit()

    # 本追加完了
    return redirect(url_for('copy_add_results',
                            code='copy-added'))


@app.route('/copy-add-results/<code>')
def copy_add_results(code: str) -> str:
    return render_template('copy-add-results.html',
                           # codeが存在しなければ'code error 'を返す
                           results=RESULT_MESSAGES.get(code, 'code error')
                           )


@app.route('/book-del/<id>')
def book_del(id: str) -> str:
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    try:
        # 文字列型で渡された本番号を整数型へ変換する
        id_num = int(id)
    except ValueError:
        # 本番号が整数型へ変換できない
        return render_template('book-del-results.html',
                               results='指定された本番号には'
                               '使えない文字があります')
    # 本番号の存在チェックをする：
    # books テーブルで同じ本番号の行を 1 行だけ取り出す
    book = cur.execute('SELECT BookID FROM Books WHERE BookID = ?',
                           (id_num,)).fetchone()
    if book is None:
        # 指定された本番号の行が無い
        return render_template('book-del-results.html',
                               results='指定された本番号は存在しません')

    # 蔵書の存在チェック：
    copy = cur.execute('SELECT CopyID FROM Copies WHERE BookID = ?',
                         (id_num,)).fetchone()

    if copy is not None:
        # 蔵書が存在する
        return render_template('book-del-results.html',
                               results='指定された本番号の本の蔵書が存在します。 - '
                                       '削除する場合は蔵書を先に削除してください')

    # 削除対象の本番号をテンプレートに渡してレンダリングしたものを返す
    return render_template('book-del.html', id=id_num)


@app.route('/book-del/<id>', methods=['POST'])
def book_del_execute(id: str):
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    try:
        # 文字列型で渡された本番号を整数型へ変換する
        id_num = int(id)
    except ValueError:
        # 本番号が整数型へ変換できない
        return redirect(url_for('book_del_results',
                                code='book-id-has-invalid-charactor'))
    # 本番号の存在チェックをする：
    # Booksテーブルで同じ本番号の行を 1 行だけ取り出す
    book = cur.execute('SELECT BookID FROM Books WHERE BookID = ?',
                           (id_num,)).fetchone()
    if book is None:
        # 指定された本番号の行が無い
        return redirect(url_for('book_del_results',
                                code='book-id-does-not-exist'))

    # 蔵書の存在チェック：
    copy = cur.execute('SELECT CopyID FROM Copies WHERE BookID = ?',
                         (id_num, )).fetchone()
    if copy is not None:
        # 蔵書が存在する
        return redirect(url_for('book_del_results',
                                code='book-is-in-library'))

    # データベースから削除
    try:
        # Books テーブルの指定された行を削除
        cur.execute('DELETE FROM Books WHERE BookID = ?', (id_num,))
    except sqlite3.Error:
        # データベースエラーが発生
        return redirect(url_for('book_add_results',
                                code='database-error'))
    # コミット（データベース更新処理を確定）
    con.commit()

    # 本追加完了
    return redirect(url_for('book_add_results',
                            code='deleted'))


@app.route('/book-del-results/<code>')
def book_del_results(code: str) -> str:
    return render_template('book-del-results.html',
                           results=RESULT_MESSAGES.get(code, 'code error'))


@app.route('/copy-del/<id>')
def copy_del(id: str) -> str:
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    try:
        # 文字列型で渡された蔵書番号を整数型へ変換する
        id_num = int(id)
    except ValueError:
        # 蔵書番号が整数型へ変換できない
        return render_template('copy-del-results.html',
                               results='指定された蔵書番号には'
                               '使えない文字があります')
    # 蔵書番号の存在チェックをする：
    # Copies テーブルで同じ本番号の行を 1 行だけ取り出す
    copy = cur.execute('SELECT CopyID FROM Copies WHERE CopyID = ?',
                           (id_num,)).fetchone()
    if copy is None:
        # 指定された蔵書番号の行が無い
        return render_template('copy-del-results.html',
                               results='指定された蔵書番号は存在しません')

    # 削除対象の本番号をテンプレートに渡してレンダリングしたものを返す
    return render_template('copy-del.html', id=id_num)


@app.route('/copy-del/<id>', methods=['POST'])
def copy_del_execute(id: str):
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    try:
        # 文字列型で渡された蔵書番号を整数型へ変換する
        id_num = int(id)
    except ValueError:
        # 蔵書番号が整数型へ変換できない
        return redirect(url_for('copy_del_results',
                                code='copy-id-has-invalid-charactor'))
    # 蔵書番号の存在チェックをする：
    # Copiesテーブルで同じ蔵書番号の行を1行だけ取り出す
    copy = cur.execute('SELECT CopyID FROM Copies WHERE CopyID = ?',
                           (id_num,)).fetchone()
    if copy is None:
        # 指定された本番号の行が無い
        return redirect(url_for('copy_del_results',
                                code='copy-id-does-not-exist'))

    # データベースから削除
    try:
        # Books テーブルの指定された行を削除
        cur.execute('DELETE FROM Copies WHERE CopyID = ?', (id_num,))
    except sqlite3.Error:
        # データベースエラーが発生
        return redirect(url_for('copy_add_results',
                                code='database-error'))
    # コミット（データベース更新処理を確定）
    con.commit()

    # 本追加完了
    return redirect(url_for('copy_add_results',
                            code='deleted'))


@app.route('/copy-del-results/<code>')
def copy_del_results(code: str) -> str:
    return render_template('copy-del-results.html',
                           results=RESULT_MESSAGES.get(code, 'code error'))


@app.route('/users')
def users() -> str:
    cur = get_db().cursor()
    coordinates = 'SELECT * FROM Users;'
    e_list = cur.execute(coordinates).fetchall()
    return render_template('users.html', e_list=e_list)


@app.route('/users', methods=['POST'])
def users_filtered() -> str:
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # Users テーブルから名前で絞り込み、
    e_list = cur.execute('SELECT * FROM Users WHERE Name LIKE ?;',
                         (request.form['user_filter'], )).fetchall()
    # 一覧をテンプレートへ渡してレンダリングしたものを返す
    return render_template('users.html', e_list=e_list)


@app.route('/users/<id>')
def user(id: str) -> str:
    con = get_db()
    cur = con.cursor()

    try:
        id_num = int(id)
    except ValueError:  # id が数値でない場合
        return render_template('user-not-found.html')

    coordinate_histories = '''
    SELECT h.CopyID, h.BorrowTime, h.ReturnTime
    FROM Histories h
    JOIN Users u ON u.UserID = h.UserID
    WHERE u.UserID = ?;
    '''
    coordinates_user = 'SELECT * FROM Users WHERE UserID = ?;'

    histories = cur.execute(coordinate_histories, (id_num, )).fetchall()
    user = cur.execute(coordinates_user, (id_num, )).fetchone()

    if user is None:  # 本が見つからなかった場合
        return render_template('user-not-found.html')

    return render_template('user.html', histories=histories, user=user)


@app.route('/user-add')
def user_add() -> str:
    # テンプレートへ何も渡さずにレンダリングしたものを返す
    return render_template('user-add.html')


@app.route('/user-add', methods=['POST'])
def user_add_execute():
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # リクエストされた POST パラメータの内容を取り出す
    user_id_str = request.form['user_id']
    name = request.form['name']
    email_address = request.form['email_address']
    phone_number = request.form['phone_number']

    # ユーザー番号チェック
    try:
        user_id = int(user_id_str)  # 文字列型で渡されたユーザー番号を整数型へ変換する
    except ValueError:
        # ユーザー番号が整数型へ変換できない
        return redirect(url_for('user_add_results',
                                code='user-id-has-invalid-charactor'))
    # ユーザー番号の存在チェックをする：
    # User テーブルで同じ本番号の行を 1 行だけ取り出す
    user = cur.execute('SELECT UserID FROM Users WHERE UserID = ?',
                           (user_id,)).fetchone()
    if user is not None:
        # 指定されたユーザー番号の行が既に存在
        return redirect(url_for('user_add_results',
                                code='user-id-already-exists'))

    # 名前チェック
    if has_control_character(name):
        # 名前に制御文字が含まれる
        return redirect(url_for('user_add_results',
                                code='name-has-control-charactor'))
    # メールチェック
    if has_control_character(email_address):
        # 名前に制御文字が含まれる
        return redirect(url_for('user_add_results',
                                code='email-address-has-control-charactor'))
    # 携帯電話チェック
    if has_control_character(phone_number):
        # 名前に制御文字が含まれる
        return redirect(url_for('user_add_results',
                                code='phone-number-has-control-charactor'))

    # データベースへユーザー情報を追加
    try:
        # Users テーブルに指定されたパラメータの行を挿入
        cur.execute('INSERT INTO Users '
                    '(UserID, Name, Email, PhoneNumber) '
                    'VALUES (?, ?, ?, ?)',
                    (user_id, name, email_address, phone_number))
    except sqlite3.Error:
        # データベースエラーが発生
        return redirect(url_for('user_add_results',
                                code='database-error'))
    # コミット（データベース更新処理を確定）
    con.commit()

    # ユーザ追加完了
    return redirect(url_for('user_add_results',
                            code='user-added'))


@app.route('/user-add-results/<code>')
def user_add_results(code: str) -> str:
    return render_template('user-add-results.html',
                           # codeが存在しなければ'code error 'を返す
                           results=RESULT_MESSAGES.get(code, 'code error')
                           )


@app.route('/borrow-add')
def borrow_add() -> str:
    # テンプレートへ何も渡さずにレンダリングしたものを返す
    return render_template('borrow-add.html')


@app.route('/borrow-add', methods=['POST'])
def borrow_add_execute():
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # リクエストされた POST パラメータの内容を取り出す
    user_id_str = request.form['user_id']
    copy_id_str = request.form['copy_id']
    borrow_time = request.form['borrow_time']

    # ユーザー番号チェック
    try:
        user_id = int(user_id_str)  # 文字列型で渡されたユーザー番号を整数型へ変換する
    except ValueError:
        # ユーザー番号が整数型へ変換できない
        return redirect(url_for('borrow_add_results',
                                code='user-id-has-invalid-charactor'))

    # copy番号チェック
    try:
        copy_id = int(copy_id_str)  # 文字列型で渡されたコピー番号を整数型へ変換する
    except ValueError:
        # ユーザー番号が整数型へ変換できない
        return redirect(url_for('borrow_add_results',
                                code='copy-id-has-invalid-charactor'))

    # 貸し出し日チェック
    if has_control_character(borrow_time):
        # 貸し出し日に制御文字が含まれる
        return redirect(url_for('borrow_add_results',
                                code='borrow-time-has-control-charactor'))

    # データベースへ貸し出し情報を追加
    try:
        # Histories テーブルに指定されたパラメータの行を挿入
        cur.execute('INSERT INTO Histories   '
                    '(CopyID, UserID, BorrowTime) '
                    'VALUES (?, ?, ?)',
                    (copy_id, user_id, borrow_time))
    except sqlite3.Error:
        # データベースエラーが発生
        return redirect(url_for('borrow_add_results',
                                code='database-error'))
    # コミット（データベース更新処理を確定）
    con.commit()

    # ユーザ追加完了
    return redirect(url_for('borrow_add_results',
                            code='borrow-added'))


@app.route('/borrow-add-results/<code>')
def borrow_add_results(code: str) -> str:
    return render_template('borrow-add-results.html',
                           # codeが存在しなければ'code error 'を返す
                           results=RESULT_MESSAGES.get(code, 'code error')
                           )


@app.route('/return-add', methods=['POST'])
def return_add_execute():
    # データベース接続してカーソルを得る
    con = get_db()
    cur = con.cursor()

    # リクエストされた POST パラメータの内容を取り出す
    return_time = request.form['return_time']
    user_id = request.form['user_id']
    copy_id = request.form['copy_id']
    borrow_time = request.form['borrow_time']

    # 返却日チェック
    if has_control_character(return_time):
        # 返却日に制御文字が含まれる
        return redirect(url_for('return_add_results',
                                code='return-time-has-control-charactor'))

    # データベースへ貸し出し情報を追加
    try:
        # Histories テーブルに指定されたパラメータの行を挿入
        cur.execute('UPDATE Histories SET ReturnTime = ? WHERE UserID = ? AND CopyID = ? AND BorrowTime = ?',
                    (return_time, user_id, copy_id, borrow_time))
    except sqlite3.Error:
        # データベースエラーが発生
        return redirect(url_for('return_add_results',
                                code='database-error'))
    # コミット（データベース更新処理を確定）
    con.commit()

    # ユーザ追加完了
    return redirect(url_for('return_add_results',
                            code='return-added'))


@app.route('/return-add-results/<code>')
def return_add_results(code: str) -> str:
    return render_template('return-add-results.html',
                           # codeが存在しなければ'code error 'を返す
                           results=RESULT_MESSAGES.get(code, 'code error')
                           )


@app.route('/history-del/<int:copy_id>/<int:user_id>/<borrow_time>', methods=['POST'])
def history_del(copy_id, user_id, borrow_time):
    con = get_db()
    cur = con.cursor()
    cur.execute('DELETE FROM Histories WHERE CopyID = ? AND UserID = ? AND BorrowTime = ?',
                (copy_id, user_id, borrow_time))
    con.commit()
    return redirect(url_for('history_del_results',
                            code='history-deleted'))


@app.route('/history-del-results/<code>')
def history_del_results(code: str) -> str:
    return render_template('history-del-results.html',
                           # codeが存在しなければ'code error 'を返す
                           results=RESULT_MESSAGES.get(code, 'code error')
                           )


@app.route('/user_del/<int:user_id>', methods=['POST'])
def user_del(user_id):
    con = get_db()
    cur = con.cursor()
    cur.execute('DELETE FROM Users WHERE UserID = ?', (user_id,))
    con.commit()
    return redirect(url_for('user_del_results',
                            code='user-deleted'))


@app.route('/user-del-results/<code>')
def user_del_results(code: str) -> str:
    return render_template('user-del-results.html',
                           # codeが存在しなければ'code error 'を返す
                           results=RESULT_MESSAGES.get(code, 'code error')
                           )


if __name__ == '__main__':
    # このスクリプトを直接実行したらデバッグ用 Web サーバで起動する
    app.run(port=8000, debug=True)