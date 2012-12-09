.. _tutorial-css:

스텝 7: 스타일 추가하기
====================

이제 모든것들이 작동한다. 이제 약간의 스타일을 어플리케이션에 추가해볼 시간이다.
전에 생성해 두었던 `static` 폴더에 `style.css` 이라고 불리는 스타일시트를 생성해서 추가해 보자:


.. sourcecode:: css

    body            { font-family: sans-serif; background: #eee; }
    a, h1, h2       { color: #377BA8; }
    h1, h2          { font-family: 'Georgia', serif; margin: 0; }
    h1              { border-bottom: 2px solid #eee; }
    h2              { font-size: 1.2em; }

    .page           { margin: 2em auto; width: 35em; border: 5px solid #ccc;
                      padding: 0.8em; background: white; }
    .entries        { list-style: none; margin: 0; padding: 0; }
    .entries li     { margin: 0.8em 1.2em; }
    .entries li h2  { margin-left: -1em; }
    .add-entry      { font-size: 0.9em; border-bottom: 1px solid #ccc; }
    .add-entry dl   { font-weight: bold; }
    .metanav        { text-align: right; font-size: 0.8em; padding: 0.3em;
                      margin-bottom: 1em; background: #fafafa; }
    .flash          { background: #CEE5F5; padding: 0.5em;
                      border: 1px solid #AACBE2; }
    .error          { background: #F0D6D6; padding: 0.5em; }

다음 섹션에서 계속 :ref:`tutorial-testing`.
