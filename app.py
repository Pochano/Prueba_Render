from flask import Flask, render_template, request, redirect, session
import json
import os
from werkzeug.security import generate_password_hash, check_password_hash

from datetime import timedelta

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "supersecretkey")

# Configurar que la sesión se cierre al cerrar el navegador
app.permanent_session_lifetime = timedelta(minutes=30)  # opcional para sesiones permanentes

usuarios_file = "usuarios.json"

# -------------------- CLASES --------------------
class Cuenta:
    def __init__(self, movimientos=None):
        if movimientos:
            self.ingresos = movimientos.get("ingresos", [])
            self.gastos = movimientos.get("gastos", [])
        else:
            self.ingresos = []
            self.gastos = []

    def agregar_ingreso(self, monto, concepto):
        if monto <= 0:
            raise ValueError("El monto del ingreso debe ser positivo")
        self.ingresos.append({"concepto": concepto, "monto": monto})

    def agregar_gasto(self, monto, concepto):
        if monto <= 0:
            raise ValueError("El monto del gasto debe ser positivo")
        self.gastos.append({"concepto": concepto, "monto": monto})

    def calcular_balance(self):
        total_ingresos = sum(i["monto"] for i in self.ingresos)
        total_gastos = sum(g["monto"] for g in self.gastos)
        return total_ingresos - total_gastos

    def obtener_detalle(self):
        return {
            "ingresos": self.ingresos,
            "gastos": self.gastos,
            "total_ingresos": sum(i["monto"] for i in self.ingresos),
            "total_gastos": sum(g["monto"] for g in self.gastos),
            "balance": self.calcular_balance()
        }

class Usuario:
    def __init__(self, nombre, movimientos=None):
        self.nombre = nombre
        self.cuenta = Cuenta(movimientos)

    def agregar_ingreso(self, monto, concepto):
        self.cuenta.agregar_ingreso(monto, concepto)

    def agregar_gasto(self, monto, concepto):
        self.cuenta.agregar_gasto(monto, concepto)

    def ver_balance(self):
        return self.cuenta.calcular_balance()

    def ver_detalle(self):
        return self.cuenta.obtener_detalle()

# -------------------- UTILIDADES --------------------
def cargar_usuarios():
    if os.path.exists(usuarios_file):
        try:
            with open(usuarios_file, "r") as f:
                contenido = f.read().strip()
                if not contenido:
                    return {}
                return json.loads(contenido)
        except json.JSONDecodeError:
            return {}
    return {}

def guardar_usuarios(usuarios):
    with open(usuarios_file, "w") as f:
        json.dump(usuarios, f, indent=4)

usuarios_objetos = {}

conceptos_gasto = [
    "Comida", "Transporte", "Educación", "Salud", "Hogar",
    "Entretenimiento", "Ropa", "Viajes", "Mascotas", "Regalos",
    "Deudas", "Impuestos", "Servicios", "Tecnología", "Otros"
]

conceptos_ingreso = [
    "Salario", "Negocio", "Bonos", "Regalos", "Inversiones",
    "Venta de cosas", "Devoluciones", "Subsidios", "Otros"
]

# -------------------- RUTAS --------------------
@app.route("/", methods=["GET", "POST"])
def login():
    mensaje = ""
    if request.method == "POST":
        usuario_input = request.form.get("usuario", "").strip()
        contrasena_input = request.form.get("contrasena", "").strip()
        accion = request.form.get("accion")

        # Validar campos vacíos
        if not usuario_input or not contrasena_input:
            mensaje = "Por favor complete todos los campos."
            return render_template("login.html", mensaje=mensaje)

        usuarios = cargar_usuarios()

        if accion == "login":
            if usuario_input in usuarios:
                if check_password_hash(usuarios[usuario_input]["password"], contrasena_input):
                    session.permanent = False  # Sesión temporal que se borra al cerrar navegador
                    session["usuario"] = usuario_input
                    movimientos = usuarios[usuario_input].get("movimientos", {})
                    usuarios_objetos[usuario_input] = Usuario(usuario_input, movimientos)
                    return redirect("/dashboard")
                else:
                    mensaje = "Contraseña incorrecta."
            else:
                mensaje = "Usuario no registrado."

        elif accion == "register":
            if usuario_input in usuarios:
                mensaje = "El usuario ya existe. Elija otro nombre."
            else:
                # Guardar nuevo usuario
                usuarios[usuario_input] = {
                    "password": generate_password_hash(contrasena_input),
                    "movimientos": {"ingresos": [], "gastos": []}
                }
                guardar_usuarios(usuarios)
                usuarios_objetos[usuario_input] = Usuario(usuario_input)
                session.permanent = False
                session["usuario"] = usuario_input
                return redirect("/dashboard")

    return render_template("login.html", mensaje=mensaje)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "usuario" not in session:
        return redirect("/")

    usuario_actual = session["usuario"]

    # Crear objeto Usuario si no existe en memoria
    if usuario_actual not in usuarios_objetos:
        usuarios = cargar_usuarios()
        movimientos = usuarios.get(usuario_actual, {}).get("movimientos", {})
        usuarios_objetos[usuario_actual] = Usuario(usuario_actual, movimientos)

    user_obj = usuarios_objetos.get(usuario_actual)
    mensaje = ""

    if request.method == "POST":
        tipo = request.form.get("tipo")
        concepto = request.form.get("concepto")
        monto_input = request.form.get("monto", "").strip()

        try:
            monto = float(monto_input)
            if monto <= 0:
                raise ValueError("El monto debe ser mayor a 0.")

            if tipo == "ingreso":
                user_obj.agregar_ingreso(monto, concepto)
            else:
                user_obj.agregar_gasto(monto, concepto)

            # Guardar solo si no hay error
            usuarios = cargar_usuarios()
            usuarios[usuario_actual]["movimientos"] = user_obj.ver_detalle()
            guardar_usuarios(usuarios)

        except ValueError as e:
            mensaje = str(e)

    detalle = user_obj.ver_detalle()
    return render_template("dashboard.html",
                           usuario=usuario_actual,
                           detalle=detalle,
                           conceptos_gasto=conceptos_gasto,
                           conceptos_ingreso=conceptos_ingreso,
                           mensaje=mensaje)

@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect("/")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000)) 
    app.run(host="0.0.0.0", port=port)