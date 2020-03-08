import os
import json
import datetime
import hashlib
from google.cloud import datastore
from flask import Flask, render_template, request, session, redirect, abort

app = Flask(__name__)
app.secret_key = 'afdyfadjknv2178y48ansj>NUdcn-^f'
jst = datetime.timezone(datetime.timedelta(hours=9), 'JST')

# クライアントの設定
client = datastore.Client.from_service_account_json(
    "fusai-kanri-teig-i-ki-b9491334a118.json")


def islogin():
    if "account" in session:
        if not client.get(client.key("account", session["account"])) is None:
            query = client.query(kind="member")
            query.add_filter("name", "=", session["account"])
            session["group"] = list(query.fetch())[0]["group"]
            return True
        else:
            del session["account"]
            return False
    else:
        return False


@app.errorhandler(404)
def notfound_(error):
    return "<script>window.location = '/group'</script>"


@app.route("/group", methods=["GET"])
def group():
    if islogin():
        pass
    else:
        redirect("/login")

    if "group" in session:
        if not "g" in request.args:
            return "<script>window.location='/group?g={0}'</script>".format(session["group"])
        query = client.query(kind="group")
        if request.args.get("g") in map(lambda n: n["name"], list(query.fetch())):
            session["group"] = request.args.get("g")
        query = client.query(kind="member")
        query.add_filter("name", "=", session["account"])
        group_list = map(lambda n: n["group"], list(query.fetch()))

        query = client.query(kind="member")
        query.add_filter("group", "=", session["group"])
        members = list(query.fetch())

        datas = list()

        for i in members:
            query = client.query(kind="debt")
            query.add_filter("group", "=", session["group"])
            query.add_filter("name", "=", i["name"])
            debts = (map(lambda n: int(n["cost"]), list(query.fetch())))
            print(debts)
            datas.append({"total": sum(debts), "name": i["name"]})

        return render_template("index.html",
                               group=session["group"],
                               user_debt=datas,
                               username=session["account"],
                               user_group=group_list)
    else:
        return render_template("notfound.html")


@app.route("/signup", methods=["GET"])
def signup():
    if islogin():
        return redirect("/group")
    return render_template("signup.html")


@app.route("/signup_2", methods=["POST"])
def signup2():
    print(request.form["passw"])
    if len(request.form["passw"]) < 8:
        result = {
            "result": {
                "result": "fail",
                "inner": "登録に失敗しました。パスワードは英数8文字以上で入力してください。<a href='/signup' class='box button'>戻る</a>"
            }
        }
        return json.dumps(result)
    elif not 3 <= len(str(request.form["name"])) <= 20:
        result = {
            "result": {
                "result": "fail",
                "inner": "登録に失敗しました。ユーザー名は3~20文字で入力してください。<a href='/signup' class='box button'>戻る</a>"
            }
        }
        return json.dumps(result)
    elif client.get(client.key("account", request.form['name'])) is not None:
        result = {
            "result": {
                "result": "fail",
                "inner": "登録に失敗しました。ユーザー名が重複しています。違うユーザー名にしてください。<a href='/signup' class='box button'>戻る</a>"
            }
        }
        return json.dumps(result)
    else:
        print(request.form["name"])
        ent = datastore.Entity(client.key(
            "account", str(request.form["name"])))
        ent["passhash1"] = hashlib.sha3_256(
            request.form['passw'].encode()).hexdigest()
        ent["passhash2"] = hashlib.md5(
            request.form['passw'].encode()).hexdigest()

        print(request.form["name"])
        ent["mailaddr"] = request.form["mailaddr"]

        client.put(ent)
        result = {
            "result": {
                "tf": "success",
                "inner": "成功しました。"
            }
        }

        session["account"] = request.form["name"]
        return json.dumps(result)


@app.route("/login")
def login():
    if islogin():
        print("this is logging in on {}".format(session["account"]))
        if "from" in request.form:
            return redirect(request.form["from"])
        else:
            return redirect("/group")
    else:
        return render_template('login.html')


@app.route("/login-verify", methods=["POST"])
def login_verify():
    if request.form["name"] == "" or not 3 <= len(request.form["name"]) <= 20:
        result = {
            "result": {
                "result": "fail",
                "inner": "ユーザー名、若しくはパスワードが異なっています。<a href='/login' class='box button'>戻る</a>"
            }
        }
        return json.dumps(result)
    elif request.form["password"] == "" or len(request.form["password"]) < 8:
        result = {
            "result": {
                "result": "fail",
                "inner": "ユーザー名、若しくはパスワードが異なっています。<a href='/login' class='box button'>戻る</a>"
            }
        }
        return json.dumps(result)
    else:
        if client.get(client.key("account", request.form['name'])) is None:
            result = {
                "result": {
                    "result": "fail",
                    "inner": "ユーザー名、若しくはパスワードが異なっています。<a href='/login' class='box button'>戻る</a>"
                }
            }
            return json.dumps(result)
        elif client.get(client.key("account", request.form['name']))["passhash1"] != hashlib.sha3_256(request.form['password'].encode()).hexdigest():
            result = {
                "result": {
                    "result": "fail",
                    "inner": "ユーザー名、若しくはパスワードが異なっています。<a href='/login' class='box button'>戻る</a>"
                }
            }
            return json.dumps(result)
        elif client.get(client.key("account", request.form['name']))["passhash2"] != hashlib.md5(request.form['password'].encode()).hexdigest():
            result = {
                "result": {
                    "result": "fail",
                    "inner": "ユーザー名、若しくはパスワードが異なっています。<a href='/login' class='box button'>戻る</a>"
                }
            }
            return json.dumps(result)
        else:
            session["account"] = request.form["name"]
            query = client.query(kind="member")
            query.add_filter("name", "=", session["account"])
            session["group"] = list(query.fetch())[0]["group"]
            result = {
                "result": {
                    "result": "success",
                    "inner": "USER VERIFIED"
                }
            }
            return json.dumps(result)


if __name__ == "__main__":
    app.run()
