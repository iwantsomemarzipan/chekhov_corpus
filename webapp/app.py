from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


# Главная страница
@app.route("/")
def main_page():
    return render_template('index.html')

# Страница с инструкцией
@app.route("/help")
def help():
    return render_template('help.html')

# Страница, перенаправляющая на репозиторий
@app.route("/repo")
def repo_redirect():
    return redirect("https://github.com/iwantsomemarzipan", code=302)


@app.route("/results", methods=["get"])
def results():
    if not request.args:
        return redirect("/")

if __name__ == '__main__':
    app.run(debug=False)