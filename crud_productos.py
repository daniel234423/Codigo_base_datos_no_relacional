from bson.objectid import ObjectId
from pymongo.errors import PyMongoError, WriteError

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

def obtener_int(mensaje, minimo=0, opcional=False, default=None):
    while True:
        entrada = input(mensaje).strip()
        if not entrada and opcional:
            return default
        try:
            valor = int(entrada)
            if valor < minimo:
                print(f"[ERROR] El número debe ser mayor o igual a {minimo}.")
                continue
            return valor
        except ValueError:
            print("[ERROR] Entrada inválida. Ingrese un número entero válido.")

def crear_producto(db):
    print("\n--- Crear Producto ---")
    nombre = input("Nombre del producto: ").strip()
    categoria = input("Categoría: ").strip()
    descripcion = input("Descripción (opcional): ").strip()
    
    if not nombre or not categoria:
        print("[ERROR] Nombre y categoría son campos obligatorios.")
        return

    precio = obtener_float("Precio (min 0): ", minimo=0.0)
    stock = obtener_int("Stock inicial (min 0): ", minimo=0)
    
    print("\n-- Datos del Proveedor --")
    prov_nombre = input("Nombre del proveedor: ").strip()
    prov_contacto = input("Contacto (email o teléfono): ").strip()
    
    if not prov_nombre or not prov_contacto:
        print("[ERROR] El proveedor debe tener nombre y contacto.")
        return

    producto = {
        "nombre": nombre,
        "categoria": categoria,
        "precio": precio,
        "stock": stock,
        "proveedor": {
            "nombre": prov_nombre,
            "contacto": prov_contacto
        }
    }
    
    if descripcion:
        producto["descripcion"] = descripcion

    try:
        resultado = db.productos.insert_one(producto)
        print(f"[ÉXITO] Producto creado con ID: {resultado.inserted_id}")
    except WriteError as we:
        print(f"\n[ERROR de Validación] MongoDB rechazó el documento por violación de esquema.")
        print(f"Detalle del error: {we.details.get('errmsg', we)}")
    except PyMongoError as e:
        print(f"\n[ERROR] Ocurrió un error en la base de datos al insertar el producto: {e}")

def listar_productos(db):
    print("\n--- Lista de Productos ---")
    try:
        productos = list(db.productos.find())
        if not productos:
            print("No hay productos registrados.")
            return []
        
        for p in productos:
            desc = f" | Desc: {p['descripcion']}" if 'descripcion' in p else ""
            print(f"ID: {p['_id']} | {p['nombre']} ({p['categoria']}) | Precio: ${p['precio']:.2f} | Stock: {p['stock']}{desc}")
            print(f"  > Proveedor: {p['proveedor']['nombre']} ({p['proveedor']['contacto']})")
        return productos
    except PyMongoError as e:
        print(f"[ERROR] Error al consultar productos: {e}")
        return []

def actualizar_producto(db):
    print("\n--- Actualizar Producto ---")
    id_str = input("Ingrese el ID del producto a actualizar: ").strip()
    try:
        producto_id = ObjectId(id_str)
    except Exception:
        print("[ERROR] El ID ingresado no tiene un formato válido de ObjectId.")
        return

    try:
        prod = db.productos.find_one({"_id": producto_id})
        if not prod:
            print("[ERROR] Producto no encontrado.")
            return

        print(f"Modificando producto: {prod['nombre']}")
        nombre = input(f"Nuevo Nombre [{prod['nombre']}]: ").strip() or prod['nombre']
        categoria = input(f"Nueva Categoría [{prod['categoria']}]: ").strip() or prod['categoria']
        
        desc_actual = prod.get('descripcion', '')
        descripcion = input(f"Nueva Descripción (dejar en blanco para omitir) [{desc_actual}]: ").strip()
        if not descripcion and desc_actual:
            descripcion = desc_actual  # Mantener actual si el usuario presionó enter directamente
        
        precio = obtener_float(f"Nuevo Precio [{prod['precio']}]: ", minimo=0.0, opcional=True, default=prod['precio'])
        stock = obtener_int(f"Nuevo Stock [{prod['stock']}]: ", minimo=0, opcional=True, default=prod['stock'])
        
        prov_actual = prod.get('proveedor', {})
        prov_nombre_act = prov_actual.get('nombre', '')
        prov_contacto_act = prov_actual.get('contacto', '')
        
        print("\n-- Modificar Proveedor --")
        prov_nombre = input(f"Nuevo Proveedor [{prov_nombre_act}]: ").strip() or prov_nombre_act
        prov_contacto = input(f"Nuevo Contacto [{prov_contacto_act}]: ").strip() or prov_contacto_act

        updates = {
            "nombre": nombre,
            "categoria": categoria,
            "precio": precio,
            "stock": stock,
            "proveedor": {
                "nombre": prov_nombre,
                "contacto": prov_contacto
            }
        }
        
        if descripcion:
            updates["descripcion"] = descripcion
        elif 'descripcion' in prod:
            # Si el producto original tenía descripción y ahora está vacío (si el usuario explícitamente quiere quitarla)
            # En este caso, el usuario dejó en blanco pero arriba dijimos que si presiona Enter mantenemos. 
            # Si quiere borrarla, podemos dejar una opción o simplemente mantenerla si no ingresa nada.
            pass

        db.productos.update_one({"_id": producto_id}, {"$set": updates})
        print("[ÉXITO] Producto actualizado correctamente.")
    except WriteError as we:
        print(f"\n[ERROR de Validación] MongoDB rechazó los cambios por violación de esquema.")
        print(f"Detalle del error: {we.details.get('errmsg', we)}")
    except PyMongoError as e:
        print(f"[ERROR] No se pudo actualizar el producto: {e}")

def eliminar_producto(db):
    print("\n--- Eliminar Producto ---")
    id_str = input("Ingrese el ID del producto a eliminar: ").strip()
    try:
        producto_id = ObjectId(id_str)
    except Exception:
        print("[ERROR] El ID ingresado no tiene un formato válido de ObjectId.")
        return

    try:
        # Verificar si está asociado a algún pedido
        pedidos_con_producto = db.pedidos.count_documents({"items.producto_id": producto_id})
        if pedidos_con_producto > 0:
            print(f"[ERROR] No se puede eliminar el producto porque está presente en {pedidos_con_producto} pedido(s).")
            return

        resultado = db.productos.delete_one({"_id": producto_id})
        if resultado.deleted_count > 0:
            print("[ÉXITO] Producto eliminado correctamente.")
        else:
            print("[ERROR] Producto no encontrado.")
    except PyMongoError as e:
        print(f"[ERROR] No se pudo eliminar el producto: {e}")

def menu_productos(db):
    while True:
        print("\n=== MENÚ PRODUCTOS ===")
        print("1. Crear Producto")
        print("2. Listar Productos")
        print("3. Actualizar Producto")
        print("4. Eliminar Producto")
        print("5. Volver al Menú Principal")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            crear_producto(db)
        elif opcion == "2":
            listar_productos(db)
        elif opcion == "3":
            actualizar_producto(db)
        elif opcion == "4":
            eliminar_producto(db)
        elif opcion == "5":
            break
        else:
            print("[ERROR] Opción no válida. Intente de nuevo.")
