# Informe Técnico: Aplicación de Consola Interactiva CRUD con MongoDB

Este documento detalla el diseño, la arquitectura, los esquemas de datos y el funcionamiento del sistema modular en Python que interactúa con una base de datos MongoDB para realizar operaciones CRUD (Crear, Leer, Actualizar y Eliminar) sobre las colecciones de **Clientes**, **Productos** y **Pedidos**.

---

## 1. Arquitectura del Proyecto

El sistema se ha estructurado de forma modular para facilitar su mantenimiento y escalabilidad. La distribución de archivos es la siguiente:

```text
Codigo_base_datos_no_relacional/
├── .venv/                      # Entorno virtual de Python
├── database.py                 # Módulo de conexión y ping a MongoDB
├── crud_clientes.py            # Operaciones CRUD para la colección 'clientes'
├── crud_productos.py           # Operaciones CRUD y validación de tipos para 'productos'
├── crud_pedidos.py             # Operaciones CRUD, control de stock y totales para 'pedidos'
├── main.py                     # Punto de entrada y menú interactivo de la consola
├── requirements.txt            # Dependencias del proyecto
└── README.md                   # Este informe técnico
```

---

## 2. Modelos de Datos y Esquemas JSON

El código está diseñado para interactuar con bases de datos MongoDB que aplican validaciones estrictas del esquema JSON (JSON Schema validation). Por ello, el código en Python realiza un pre-procesamiento (casteo) de los datos de entrada por consola a los tipos de datos correctos antes de realizar las llamadas a la base de datos.

### A. Colección `clientes`
*   `nombre` (string): Nombre completo del cliente.
*   `rut` (string): Identificador único chileno (RUT/DNI).
*   `email` (string): Dirección de correo electrónico.
*   `telefono` (string, opcional): Número de contacto.

### B. Colección `productos`
*   `nombre` (string): Nombre comercial.
*   `categoria` (string): Categoría del producto.
*   `descripcion` (string, opcional): Explicación breve del artículo.
*   `precio` (float, mínimo 0): Costo unitario.
*   `stock` (int, mínimo 0): Cantidad disponible en el inventario.
*   `proveedor` (object): Subdocumento embebido con:
    *   `nombre` (string)
    *   `contacto` (string)

### C. Colección `pedidos`
*   `cliente_id` (ObjectId): Referencia a un cliente en la colección `clientes`.
*   `fecha_pedido` (date): Fecha y hora del registro (UTC).
*   `estado` (string): Estado del pedido, limitado a: `["pendiente", "procesado", "enviado", "cancelado"]`.
*   `items` (array de objects): Productos solicitados. Cada objeto contiene:
    *   `producto_id` (ObjectId): Referencia en la colección `productos`.
    *   `cantidad` (int, mínimo 1): Unidades solicitadas.
    *   `precio_unitario` (float, mínimo 0): Precio del producto al momento de comprar.
*   `total` (float, mínimo 0): Suma acumulada de `cantidad * precio_unitario` de todos los items.
*   `metodo_pago` (string): Canal de pago, limitado a: `["tarjeta_credito", "transferencia", "efectivo"]`.
*   `direccion_envio` (object): Datos de despacho:
    *   `calle` (string), `ciudad` (string), `region` (string), `codigo_postal` (string).

---

## 3. Explicación del Código y Ejemplos

### A. Conexión Resiliente (`database.py`)
Establece la conexión utilizando `pymongo.MongoClient`. Para evitar bloqueos eternos si el servidor local de MongoDB no está activo, se define un timeout de selección de servidor de 3 segundos (`serverSelectionTimeoutMS`) y se realiza un `ping` inmediato.

```python
# Ejemplo de conexión y verificación en database.py
def get_db():
    try:
        # Se establece un timeout corto (3 segundos) para verificar conexión rápidamente
        client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=3000)
        # Forzar una llamada para comprobar la conexión activa
        client.admin.command('ping')
        return client[DB_NAME]
    except ConnectionFailure:
        print("\n[ERROR] No se pudo establecer conexión con el servidor de MongoDB.")
        sys.exit(1)
```

### B. Validación y Conversión de Tipos de Entrada (`crud_productos.py`)
Para cumplir las restricciones numéricas (`minimo=0`), se crearon funciones de utilidad reutilizables que capturan errores de casteo (`ValueError`) de forma recursiva hasta que el usuario provee un valor correcto.

```python
# Helper para entradas de tipo float en crud_productos.py
def obtener_float(mensaje, minimo=0.0, opcional=False, default=None):
    while True:
        entrada = input(mensaje).strip()
        if not entrada and opcional:
            return default
        try:
            valor = float(entrada)
            if valor < minimo:
                print(f"[ERROR] El número debe ser mayor o igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("[ERROR] Entrada inválida. Ingrese un número decimal válido.")
```

### C. Lógica de Pedidos, Integridad Referencial y Stock (`crud_pedidos.py`)
El módulo de pedidos realiza tareas avanzadas para asegurar la integridad de la base de datos:
1.  **Validación de existencia del Cliente**: Verifica que el `cliente_id` ingresado corresponda a un cliente existente.
2.  **Validación de stock del Producto**: Compara la cantidad solicitada con la cantidad en almacén.
3.  **Actualización transaccional de stock**: Al crearse un pedido, se descuenta de forma automática el stock (`$inc` con valor negativo) de los productos del pedido.
4.  **Cálculo automático del total**: Calcula el precio final basándose en el precio unitario consultado del producto.

```python
# Flujo de creación de pedido y actualización de stock en crud_pedidos.py
def crear_pedido(db):
    ...
    # Se obtienen los datos del producto directamente de la DB para garantizar consistencia
    producto = db.productos.find_one({"_id": prod_id})
    precio_unitario = producto['precio']
    
    items.append({
        "producto_id": prod_id,
        "cantidad": cantidad,
        "precio_unitario": float(precio_unitario)
    })
    total += cantidad * precio_unitario
    ...
    # Registrar el pedido e incrementar negativamente el stock
    db.pedidos.insert_one(pedido)
    for item in items:
        db.productos.update_one(
            {"_id": item["producto_id"]},
            {"$inc": {"stock": -item["cantidad"]}}
        )
```

Al **eliminar** un pedido, el sistema consulta interactivamente si se desea devolver la cantidad comprada al inventario de productos:

```python
# Reposición opcional de stock al eliminar en crud_pedidos.py
if reponer_stock == 's':
    for item in pedido["items"]:
        db.productos.update_one(
            {"_id": item["producto_id"]},
            {"$inc": {"stock": item["cantidad"]}}
        )
```

---

## 4. Captura de Errores de Validación (MongoDB Schema)

Todas las funciones críticas de inserción (`insert_one`) o modificación (`update_one`) están protegidas con bloques `try-except` para atrapar fallos provocados por el validador JSON interno de MongoDB (`pymongo.errors.WriteError`).

```python
try:
    resultado = db.productos.insert_one(producto)
except WriteError as we:
    print(f"\n[ERROR de Validación] MongoDB rechazó el documento por violación de esquema.")
    print(f"Detalle del error: {we.details.get('errmsg', we)}")
```

---

## 5. Guía de Uso del Menú Principal (`main.py`)

El archivo principal interactúa con los módulos mediante un bucle interactivo clásico:

```python
# Integración de menús en main.py
def main():
    db = get_db()
    while True:
        print("\n==================================")
        print("   SISTEMA DE GESTIÓN DE VENTAS")
        print("==================================")
        print("1. Gestionar Clientes")
        print("2. Gestionar Productos")
        print("3. Gestionar Pedidos")
        print("4. Salir")
        ...
        opcion = input("Seleccione una opción: ").strip()
        if opcion == "1":
            menu_clientes(db)
        ...
```

---

## 6. Instalación y Ejecución Rápida

### Requisitos Previos
*   Tener instalado Python 3.x
*   Tener un servidor MongoDB en ejecución en `localhost:27017`

### Pasos para iniciar

1.  **Clonar/Abrir el directorio del proyecto**:
    ```bash
    cd Codigo_base_datos_no_relacional
    ```

2.  **Activar el entorno virtual**:
    *   **Windows**:
        ```powershell
        .\.venv\Scripts\activate
        ```
    *   **Linux/macOS**:
        ```bash
        source .venv/bin/activate
        ```

3.  **Instalar dependencias**:
    ```bash
    pip install -r requirements.txt
    ```

4.  **Iniciar la aplicación**:
    ```bash
    python main.py
    ```