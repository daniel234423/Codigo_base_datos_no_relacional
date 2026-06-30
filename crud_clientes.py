from bson.objectid import ObjectId
from pymongo.errors import PyMongoError

def crear_cliente(db):
    print("\n--- Crear Cliente ---")
    nombre = input("Nombre: ").strip()
    rut = input("RUT: ").strip()
    email = input("Email: ").strip()
    telefono = input("Teléfono: ").strip()

    if not nombre or not rut or not email:
        print("[ERROR] El nombre, RUT y email son campos obligatorios.")
        return

    cliente = {
        "nombre": nombre,
        "rut": rut,
        "email": email,
        "telefono": telefono
    }

    try:
        resultado = db.clientes.insert_one(cliente)
        print(f"[ÉXITO] Cliente creado con ID: {resultado.inserted_id}")
    except PyMongoError as e:
        print(f"[ERROR] No se pudo crear el cliente en MongoDB: {e}")

def listar_clientes(db):
    print("\n--- Lista de Clientes ---")
    try:
        clientes = list(db.clientes.find())
        if not clientes:
            print("No hay clientes registrados.")
            return []
        
        for c in clientes:
            print(f"ID: {c['_id']} | Nombre: {c['nombre']} | RUT: {c['rut']} | Email: {c['email']} | Tel: {c.get('telefono', 'N/A')}")
        return clientes
    except PyMongoError as e:
        print(f"[ERROR] Error al consultar clientes: {e}")
        return []

def actualizar_cliente(db):
    print("\n--- Actualizar Cliente ---")
    id_str = input("Ingrese el ID del cliente a actualizar: ").strip()
    try:
        cliente_id = ObjectId(id_str)
    except Exception:
        print("[ERROR] El ID ingresado no tiene un formato válido de ObjectId.")
        return

    try:
        cliente = db.clientes.find_one({"_id": cliente_id})
        if not cliente:
            print("[ERROR] Cliente no encontrado.")
            return

        print(f"Modificando cliente: {cliente['nombre']}")
        nombre = input(f"Nuevo Nombre [{cliente['nombre']}]: ").strip() or cliente['nombre']
        rut = input(f"Nuevo RUT [{cliente['rut']}]: ").strip() or cliente['rut']
        email = input(f"Nuevo Email [{cliente['email']}]: ").strip() or cliente['email']
        telefono = input(f"Nuevo Teléfono [{cliente.get('telefono', '')}]: ").strip() or cliente.get('telefono', '')

        updates = {
            "nombre": nombre,
            "rut": rut,
            "email": email,
            "telefono": telefono
        }

        db.clientes.update_one({"_id": cliente_id}, {"$set": updates})
        print("[ÉXITO] Cliente actualizado correctamente.")
    except PyMongoError as e:
        print(f"[ERROR] No se pudo actualizar el cliente: {e}")

def eliminar_cliente(db):
    print("\n--- Eliminar Cliente ---")
    id_str = input("Ingrese el ID del cliente a eliminar: ").strip()
    try:
        cliente_id = ObjectId(id_str)
    except Exception:
        print("[ERROR] El ID ingresado no tiene un formato válido de ObjectId.")
        return

    try:
        # Verificar si hay pedidos asociados para advertir
        pedidos_asociados = db.pedidos.count_documents({"cliente_id": cliente_id})
        if pedidos_asociados > 0:
            print(f"[ADVERTENCIA] Este cliente tiene {pedidos_asociados} pedido(s) asociado(s).")
            confirmar = input("¿Está seguro de que desea eliminarlo? (s/n): ").strip().lower()
            if confirmar != 's':
                print("Operación cancelada.")
                return

        resultado = db.clientes.delete_one({"_id": cliente_id})
        if resultado.deleted_count > 0:
            print("[ÉXITO] Cliente eliminado correctamente.")
        else:
            print("[ERROR] Cliente no encontrado.")
    except PyMongoError as e:
        print(f"[ERROR] No se pudo eliminar el cliente: {e}")

def menu_clientes(db):
    while True:
        print("\n=== MENÚ CLIENTES ===")
        print("1. Crear Cliente")
        print("2. Listar Clientes")
        print("3. Actualizar Cliente")
        print("4. Eliminar Cliente")
        print("5. Volver al Menú Principal")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            crear_cliente(db)
        elif opcion == "2":
            listar_clientes(db)
        elif opcion == "3":
            actualizar_cliente(db)
        elif opcion == "4":
            eliminar_cliente(db)
        elif opcion == "5":
            break
        else:
            print("[ERROR] Opción no válida. Intente de nuevo.")
