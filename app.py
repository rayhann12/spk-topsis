from flask import Flask, render_template, request, redirect, url_for, session
from db import get_connection
from topsis.topsis import calculate_topsis

app = Flask(__name__)
app.secret_key = "secretkey123"

# =====================
# LOGIN
# =====================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (request.form["username"], request.form["password"])
        )
        user = cursor.fetchone()

        cursor.close()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]

            return redirect(
                url_for("admin_dashboard")
                if user["role"] == "admin"
                else url_for("penilai_dashboard")
            )

        return render_template("login.html", error="Username atau password salah")

    return render_template("login.html")


# =====================
# DASHBOARD
# =====================
@app.route("/admin")
def admin_dashboard():
    if session.get("role") != "admin":
        return redirect(url_for("login"))
    return render_template("admin_dashboard.html")


@app.route("/penilai")
def penilai_dashboard():
    if session.get("role") != "penilai":
        return redirect(url_for("login"))
    return render_template("penilai_dashboard.html")


# =====================
# KELOLA USER (ADMIN)
# =====================
@app.route("/admin/users")
def user_list():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("user_list.html", users=users)


@app.route("/admin/users/add", methods=["GET", "POST"])
def user_add():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (username, password, role) VALUES (%s,%s,%s)",
            (request.form["username"], request.form["password"], request.form["role"])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("user_list"))

    return render_template("user_form.html", mode="add")


@app.route("/admin/users/edit/<int:id>", methods=["GET", "POST"])
def user_edit(id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if request.method == "POST":
        cursor.execute(
            "UPDATE users SET username=%s, password=%s, role=%s WHERE id=%s",
            (request.form["username"], request.form["password"], request.form["role"], id)
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("user_list"))

    cursor.execute("SELECT * FROM users WHERE id=%s", (id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template("user_form.html", mode="edit", user=user)


@app.route("/admin/users/delete/<int:id>")
def user_delete(id):
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM users WHERE id=%s", (id,))
    conn.commit()
    cursor.close()
    conn.close()

    return redirect(url_for("user_list"))


# =====================
# KELOLA KRITERIA (ADMIN)
# =====================
@app.route("/admin/criteria")
def criteria_list():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM criteria")
    criteria = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("criteria_list.html", criteria=criteria)


@app.route("/admin/criteria/add", methods=["GET", "POST"])
def criteria_add():
    if session.get("role") != "admin":
        return redirect(url_for("login"))

    if request.method == "POST":
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO criteria (nama_kriteria, bobot, jenis) VALUES (%s,%s,%s)",
            (request.form["nama_kriteria"], request.form["bobot"], request.form["jenis"])
        )
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("criteria_list"))

    return render_template("criteria_form.html", mode="add")


# =====================
# INPUT NILAI (PENILAI)
# =====================
@app.route("/penilai/input", methods=["GET", "POST"])
def input_nilai():
    if session.get("role") != "penilai":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM alternatives")
    alternatives = cursor.fetchall()

    cursor.execute("SELECT * FROM criteria")
    criteria = cursor.fetchall()

    if request.method == "POST":
        alternative_id = request.form["alternative_id"]

        for c in criteria:
            nilai = request.form.get(f"nilai_{c['id']}")
            cursor.execute(
                "INSERT INTO scores (alternative_id, criteria_id, nilai) VALUES (%s,%s,%s)",
                (alternative_id, c["id"], nilai)
            )

        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("penilai_dashboard"))

    cursor.close()
    conn.close()
    return render_template("input_nilai.html", alternatives=alternatives, criteria=criteria)


# =====================
# HITUNG TOPSIS (PENILAI)
# =====================
@app.route("/penilai/topsis/hitung")
def hitung_topsis():
    if session.get("role") != "penilai":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM alternatives")
    alternatives = cursor.fetchall()

    cursor.execute("SELECT * FROM criteria")
    criteria = cursor.fetchall()

    matrix = []
    for alt in alternatives:
        row = []
        for c in criteria:
            cursor.execute(
                "SELECT nilai FROM scores WHERE alternative_id=%s AND criteria_id=%s",
                (alt["id"], c["id"])
            )
            nilai = cursor.fetchone()
            row.append(float(nilai["nilai"]) if nilai else 0)
        matrix.append(row)

    weights = [float(c["bobot"]) for c in criteria]
    types = [c["jenis"] for c in criteria]

    ranking, preference = calculate_topsis(matrix, weights, types)

    # reset tabel ranking
    cursor.execute("DELETE FROM ranking")

    for i, alt in enumerate(alternatives):
        cursor.execute(
            "INSERT INTO ranking (alternative_id, nilai, ranking) VALUES (%s,%s,%s)",
            (alt["id"], float(preference[i]), int(ranking[i]))
        )

    conn.commit()
    cursor.close()
    conn.close()

    # ⬅️ LANGSUNG PINDAH, TANPA TAMPILAN
    return redirect(url_for("lihat_peringkat"))

# =====================
# LIHAT PERINGKAT (PENILAI)
# =====================
@app.route("/penilai/peringkat")
def lihat_peringkat():
    if session.get("role") != "penilai":
        return redirect(url_for("login"))

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.nama, r.nilai, r.ranking
        FROM ranking r
        JOIN alternatives a ON r.alternative_id = a.id
        ORDER BY r.ranking ASC
    """)

    hasil = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template("peringkat.html", hasil=hasil)



# =====================
# LOGOUT
# =====================
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
