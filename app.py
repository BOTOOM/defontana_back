from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import text
from dataclasses import dataclass, field, asdict
from flask import jsonify # <- `jsonify` instead of `json`
from datetime import datetime, timedelta
from sqlalchemy import func

import pyodbc
print(pyodbc.drivers())

app = Flask(__name__)

SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://ReadOnly:d*3PSf2MmRX9vJtA5sgwSphCVQ26*T53uU@lab-defontana-202310.caporvnn6sbh.us-east-1.rds.amazonaws.com:1433/Prueba?driver=ODBC+Driver+17+for+SQL+Server"
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


@dataclass
class MainDataClass:
    @property
    def to_dict(self):
        """
        get a python dictionary
        """
        return asdict(self)

class Venta(db.Model):
    __tablename__ = 'Venta'

    ID_Venta = db.Column(db.Integer, primary_key=True)
    Total = db.Column(db.Float)
    Fecha = db.Column(db.DateTime(timezone=True), nullable=True)
    ID_Local = db.Column(db.Integer)

@dataclass
class VentaData(MainDataClass):
    ID_Venta: int  # type: ignore
    Total: float
    Fecha: datetime
    ID_Local: int

@dataclass
class LocalData(MainDataClass):
    ID_Local: int
    Nombre: str
    Direccion: str

class Local(db.Model):
    __tablename__ = 'Local'
    ID_Local = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String)
    Direccion = db.Column(db.String)

@dataclass
class MarcaData(MainDataClass):
    ID_Marca: int
    Nombre: str

class Marca(db.Model):
    __tablename__ = 'Marca'
    ID_Marca = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String)

@dataclass
class ProductoData(MainDataClass):
    ID_Producto: int
    Nombre: str
    Codigo: str
    ID_Marca: int
    Modelo: str
    Costo_Unitario: int

class Producto(db.Model):
    __tablename__ = 'Producto'
    ID_Producto = db.Column(db.Integer, primary_key=True)
    Nombre = db.Column(db.String)
    Codigo = db.Column(db.String)
    ID_Marca = db.Column(db.Integer, db.ForeignKey('Marca.ID_Marca'))
    Modelo = db.Column(db.String)
    Costo_Unitario = db.Column(db.Integer)

@dataclass
class VentaDetalleData(MainDataClass):
    ID_VentaDetalle: int
    ID_Venta: int
    Precio_Unitario: int
    Cantidad: int
    TotalLinea: int
    ID_Producto: int

class VentaDetalle(db.Model):
    __tablename__ = 'VentaDetalle'
    ID_VentaDetalle = db.Column(db.Integer, primary_key=True)
    ID_Venta = db.Column(db.Integer, db.ForeignKey('Venta.ID_Venta'))
    Precio_Unitario = db.Column(db.Integer)
    Cantidad = db.Column(db.Integer)
    TotalLinea = db.Column(db.Integer)
    ID_Producto = db.Column(db.Integer, db.ForeignKey('Producto.ID_Producto'))

@app.route('/ventas')
def get_ventas():
    """
    Consulta todos los registros de la tabla Venta. 
    """
    past_30_days = datetime.now() - timedelta(days=30)
    print("pasados", past_30_days)
    ventas = Venta.query.filter(
        Venta.Fecha >= past_30_days,
        Venta.Fecha < datetime.now()
        ).all()
    lista = []
    for venta in ventas:
        lista.append(VentaData(ID_Venta=venta.ID_Venta, Total=venta.Total,Fecha=venta.Fecha,ID_Local=venta.ID_Local))
    return {"status": 200, "data": lista}

# Endpoint para obtener el total de ventas de los últimos 30 días
@app.route('/total_ventas_ultimos_30_dias')
def total_ventas_ultimos_30_dias():
    past_30_days = datetime.now() - timedelta(days=30)

    total_ventas = Venta.query.filter(
        Venta.Fecha >= past_30_days,
        Venta.Fecha < datetime.now()
    ).count()

    monto_total_ventas = Venta.query.filter(
        Venta.Fecha >= past_30_days,
        Venta.Fecha < datetime.now()
    ).with_entities(func.sum(Venta.Total)).scalar()

    return {"status": 200, "total_ventas": total_ventas, "monto_total_ventas": monto_total_ventas}

# Endpoint para obtener el día y hora de la venta con el monto más alto
@app.route('/venta_mayor_monto')
def venta_mayor_monto():
    venta_mayor_monto = Venta.query.order_by(Venta.Total.desc()).first()

    return {"status": 200, "fecha_hora_venta_mayor_monto": venta_mayor_monto.Fecha, "monto_mayor": venta_mayor_monto.Total}

# Endpoint para obtener el producto con mayor monto total de ventas
@app.route('/producto_mayor_monto_total_ventas')
def producto_mayor_monto_total_ventas():
    result = db.session.query(
        Producto,
        func.sum(VentaDetalle.TotalLinea).label('monto_total_ventas')
    ).join(VentaDetalle, Producto.ID_Producto == VentaDetalle.ID_Producto).group_by(Producto.ID_Producto, Producto.Nombre, Producto.Codigo, Producto.ID_Marca, Producto.Modelo, Producto.Costo_Unitario).order_by(func.sum(VentaDetalle.TotalLinea).desc()).first()
    producto_mayor_monto_total_ventas = ProductoData(
        ID_Producto=result[0].ID_Producto,
        Nombre=result[0].Nombre,
        Codigo =result[0].Codigo,
        ID_Marca = result[0].ID_Marca,
        Modelo = result[0].Modelo,
        Costo_Unitario = result[0].Costo_Unitario,
    )
    return {"status": 200,  "monto_total_ventas": result[1], "producto":producto_mayor_monto_total_ventas}

# Endpoint para obtener el local con mayor monto de ventas
@app.route('/local_mayor_monto_ventas')
def local_mayor_monto_ventas():
    result = db.session.query(
        Local,
        func.sum(Venta.Total).label('monto_total_ventas')
    ).join(Venta, Local.ID_Local == Venta.ID_Local).group_by(Local.ID_Local, Local.Nombre, Local.Direccion).order_by(func.sum(Venta.Total).desc()).first()
    local_mayor_monto_ventas = LocalData(
        ID_Local = result[0].ID_Local,
        Nombre = result[0].Nombre,
        Direccion = result[0].Direccion,
    )
    return {"status": 200, "local": local_mayor_monto_ventas, "monto_total_ventas": result[1]}

# Endpoint para obtener la marca con mayor margen de ganancias
@app.route('/marca_mayor_margen_ganancias')
def marca_mayor_margen_ganancias():
    result = db.session.query(
        Marca,
        func.sum((VentaDetalle.Cantidad * VentaDetalle.Precio_Unitario) - (VentaDetalle.Cantidad * Producto.Costo_Unitario)).label('margen_ganancias')
    ).join(Producto, Marca.ID_Marca == Producto.ID_Marca).join(VentaDetalle, Producto.ID_Producto == VentaDetalle.ID_Producto).group_by(Marca.ID_Marca, Marca.Nombre).order_by(func.sum((VentaDetalle.Cantidad * VentaDetalle.Precio_Unitario) - (VentaDetalle.Cantidad * Producto.Costo_Unitario)).desc()).first()
    marca_mayor_margen_ganancias = MarcaData(
        ID_Marca= result[0].ID_Marca,
        Nombre= result[0].Nombre,
    ) 
    return {"status": 200, "marca": marca_mayor_margen_ganancias, "margen_ganancias": result[1]}

def subconsulta_ventas_por_local():
    subquery = (
        select([
            Venta.c.ID_Local,
            VentaDetalle.c.ID_Producto,
            func.sum(VentaDetalle.c.Cantidad).label('total_vendido')
        ])
        .select_from(Venta.join(VentaDetalle, Venta.c.ID_Venta == VentaDetalle.c.ID_Venta))
        .group_by(Venta.c.ID_Local, VentaDetalle.c.ID_Producto)
        .alias('VentasPorLocal')
    )
    return subquery

# Endpoint para obtener el producto más vendido en cada local
@app.route('/producto_mas_vendido_por_local')
def producto_mas_vendido_por_local():
    subquery = db.session.query(
        Venta.ID_Local,
        VentaDetalle.ID_Producto,
        func.sum(VentaDetalle.Cantidad).label('total_vendido')
    ).join(VentaDetalle, Venta.ID_Venta == VentaDetalle.ID_Venta).group_by(Venta.ID_Local, VentaDetalle.ID_Producto).subquery()

    productos_mas_vendidos = db.session.query(
        Local,
        Producto,
        subquery.c.total_vendido
    ).join(subquery, Local.ID_Local == subquery.c.ID_Local).join(Producto, subquery.c.ID_Producto == Producto.ID_Producto).order_by(Local.ID_Local, subquery.c.total_vendido.desc()).group_by(
        Local.ID_Local,
        Producto.ID_Producto,
        Local.Nombre,
        Local.Direccion,
        Producto.Nombre,
        Producto.Codigo,
        Producto.ID_Marca,
        Producto.Modelo,
        Producto.Costo_Unitario,
        subquery.c.total_vendido
        ).all()

    resultado = []
    for local, producto, total_vendido in productos_mas_vendidos:
        print(total_vendido)
        resultado.append({
            "local": LocalData(
                ID_Local = local.ID_Local,
                Nombre = local.Nombre,
                Direccion = local.Direccion),
            "producto": ProductoData(
                ID_Producto=producto.ID_Producto,
                Nombre=producto.Nombre,
                Codigo =producto.Codigo,
                ID_Marca = producto.ID_Marca,
                Modelo = producto.Modelo,
                Costo_Unitario = producto.Costo_Unitario,
                ),
            "total_vendido": total_vendido
        })

    return {"status": 200, "productos_mas_vendidos_por_local": resultado}

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


