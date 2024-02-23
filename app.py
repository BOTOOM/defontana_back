from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import text
from dataclasses import dataclass, field, asdict
from flask import jsonify # <- `jsonify` instead of `json`
from datetime import datetime, timedelta

import pyodbc
print(pyodbc.drivers())

app = Flask(__name__)

# Configuración de la conexión a SQL Server
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://driver=ODBC+Driver+17+for+SQL+Server;ReadOnly:d*3PSf2MmRX9vJtA5sgwSphCVQ26*T53uU@lab-defontana-202310.caporvnn6sbh.us-east-1.rds.amazonaws.com:1433/Prueba'
# SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://lab-defontana-202310.caporvnn6sbh.us-east-1.rds.amazonaws.com:1433/Prueba?driver=ODBC+Driver+18+for+SQL+Server?trusted_connection=yes?UID" \
#                               "=ReadOnly?PWD=d*3PSf2MmRX9vJtA5sgwSphCVQ26*T53uU"
SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://ReadOnly:d*3PSf2MmRX9vJtA5sgwSphCVQ26*T53uU@lab-defontana-202310.caporvnn6sbh.us-east-1.rds.amazonaws.com:1433/Prueba?driver=ODBC+Driver+17+for+SQL+Server"
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://ReadOnly:d*3PSf2MmRX9vJtA5sgwSphCVQ26*T53uU@lab-defontana-202310.caporvnn6sbh.us-east-1.rds.amazonaws.com:1433/Prueba'
app.config['SQLALCHEMY_DATABASE_URI'] = SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

print("cosito", app.config['SQLALCHEMY_DATABASE_URI'])
db_engine = create_engine(
    app.config['SQLALCHEMY_DATABASE_URI']
)
db_session = scoped_session(
    sessionmaker(bind=db_engine, autocommit=False, autoflush=True)
)

db = SQLAlchemy()

with app.app_context():
    db.init_app(app)
    print("init db")


# db = SQLAlchemy(app)


@dataclass
class MainDataClass:
    @property
    def to_dict(self):
        """
        get a python dictionary
        """
        return asdict(self)

# Definición del modelo de la tabla Venta
class Venta(db.Model):
    __tablename__ = 'Venta'

    ID_Venta = db.Column(db.Integer, primary_key=True)
    Total = db.Column(db.Float)
    # Neto = db.Column(db.Float)
    Fecha = db.Column(db.DateTime(timezone=True), nullable=True)
    # Iva = db.Column(db.Float)
    ID_Local = db.Column(db.Integer)

@dataclass
class VentaData(MainDataClass):
    ID_Venta: int  # type: ignore
    Total: float
    Fecha: datetime
    ID_Local: int

# @app.route('/ventas')
# def get_ventas():
#     """
#     Consulta todos los registros de la tabla Venta.
#     """
#     ventas = Venta.query.all()
#     return jsonify([venta.to_dict() for venta in ventas])

@app.route('/ventas')
def get_ventas():
    """
    Consulta todos los registros de la tabla Venta. 
    """
    past_30_days = datetime.now() - timedelta(days=30)
    print("pasados", past_30_days)
    # Execute query using SQLAlchemy filter for filtering by date
    ventas = Venta.query.filter(
        Venta.Fecha >= past_30_days,
        Venta.Fecha < datetime.now()
        ).all()
    # Convierte los resultados a una lista de diccionarios
    lista = []
    for venta in ventas:
        lista.append(VentaData(ID_Venta=venta.ID_Venta, Total=venta.Total,Fecha=venta.Fecha,ID_Local=venta.ID_Local))
    # for venta in ventas:
    #     print(venta.ID_Venta,venta.Total )
    # resultados = [dict(row) for row in ventas]

    # return jsonify([venta.to_dict() for venta in ventas])
    return {"status": 200, "data": lista}

# @app.route('/venta/<int:id_venta>')
# def get_venta_por_id(id_venta):
#     """
#     Consulta un registro de la tabla Venta por su ID.
#     """
#     venta = Venta.query.get(id_venta)
#     if venta is None:
#         return jsonify({"error": "Venta no encontrada"}), 404
#     return jsonify(venta.to_dict())

# if __name__ == '__main__':
#     print("holoo")
#     app.run(debug=True)

@app.route("/")
def index():
    """Home endpoint
    Simple test endpoint.
    ---
    responses:
        500:
            description: Error The number is not integer!
        200:
            description: Good response
    """

    return "This is a test response"


