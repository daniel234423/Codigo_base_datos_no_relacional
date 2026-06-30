from bson.objectid import ObjectId
from datetime import datetime, timezone
from pymongo.errors import PyMongoError, WriteError

def obtener_estado():
    estados = ["pendiente", "procesado", "enviado", "cancelado"]
    while True:
        print("\nSeleccione el estado del pedido:")
        for idx, est in enumerate(estados, 1):
            print(f"{idx}. {est.capitalize()}")
        opcion = input("Opción: ").strip()
        try:
            opc = int(opcion)
            if 1 <= opc <= len(estados):
                return estados[opc - 1]
        except ValueError:
            pass
        print("[ERROR] Opción inválida. Seleccione un número de la lista.")

def obtener_metodo_pago():
    metodos = {
        "1": ("tarjeta_credito", "Tarjeta de Crédito"),
        "2": ("transferencia", "Transferencia"),
        "3": ("efectivo", "Efectivo")
    }
    while True:
        print("\nSeleccione el método de pago:")
        for k, v in metodos.items():
            print(f"{k}. {v[1]}")
        opcion = input("Opción: ").strip()
        if opcion in metodos:
            return metodos[opcion][0]
        print("[ERROR] Opción inválida. Ingrese una de las opciones numéricas.")

def crear_pedido(db):
    print("\n--- Crear Pedido ---")
    
    # 1. Validar Cliente
    cliente_id_str = input("Ingrese el ID del cliente (ObjectId): ").strip()
    try:
        cliente_id = ObjectId(cliente_id_str)
    except Exception:
        print("[ERROR] El ID del cliente no tiene un formato válido de ObjectId.")
        return

    # Verificar si el cliente existe en la colección
    cliente = db.clientes.find_one({"_id": cliente_id})
    if not cliente:
        print(f"[ERROR] No existe ningún cliente con el ID {cliente_id} en la base de datos.")
        return
    print(f"Cliente seleccionado: {cliente['nombre']}")

    # 2. Agregar Items (Productos)
    items = []
    total = 0.0

    while True:
        print("\n-- Agregar Producto al Pedido --")
        prod_id_str = input("Ingrese el ID del producto (ObjectId): ").strip()
        try:
            prod_id = ObjectId(prod_id_str)
        except Exception:
            print("[ERROR] El ID del producto no tiene un formato válido de ObjectId.")
            continue

        # Verificar si el producto existe
        producto = db.productos.find_one({"_id": prod_id})
        if not producto:
            print(f"[ERROR] No existe ningún producto con el ID {prod_id}.")
            continue

        print(f"Producto: {producto['nombre']} | Precio base: ${producto['precio']:.2f} | Stock disponible: {producto['stock']}")
        
        if producto['stock'] <= 0:
            print("[ERROR] Este producto no tiene stock disponible.")
            continue

        # Cantidad
        while True:
            cant_str = input(f"Cantidad (mínimo 1, stock {producto['stock']}): ").strip()
            try:
                cantidad = int(cant_str)
                if cantidad < 1:
                    print("[ERROR] La cantidad debe ser mayor o igual a 1.")
                    continue
                if cantidad > producto['stock']:
                    print(f"[ADVERTENCIA] La cantidad solicitada ({cantidad}) supera el stock disponible ({producto['stock']}).")
                    confirmar = input("¿Desea continuar de todos modos? (s/n): ").strip().lower()
                    if confirmar != 's':
                        continue
                break
            except ValueError:
                print("[ERROR] Ingrese un número entero válido.")

        precio_unitario = producto['precio']
        items.append({
            "producto_id": prod_id,
            "cantidad": cantidad,
            "precio_unitario": float(precio_unitario)
        })
        total += cantidad * precio_unitario
        print(f"[AÑADIDO] {producto['nombre']} x{cantidad} agregado. Subtotal: ${cantidad * precio_unitario:.2f}")

        otro = input("\n¿Desea agregar otro producto a este pedido? (s/n): ").strip().lower()
        if otro != 's':
            break

    if not items:
        print("[ERROR] No se puede registrar un pedido sin items.")
        return

    # 3. Dirección de Envío
    print("\n-- Dirección de Envío --")
    calle = input("Calle y Número: ").strip()
    ciudad = input("Ciudad: ").strip()
    region = input("Región: ").strip()
    codigo_postal = input("Código Postal: ").strip()

    if not calle or not ciudad or not region or not codigo_postal:
        print("[ERROR] Todos los campos de la dirección de envío son obligatorios.")
        return

    direccion_envio = {
        "calle": calle,
        "ciudad": ciudad,
        "region": region,
        "codigo_postal": codigo_postal
    }

    # 4. Método de Pago y Estado
    metodo_pago = obtener_metodo_pago()
    estado = "pendiente"  # Estado por defecto al crear

    pedido = {
        "cliente_id": cliente_id,
        "fecha_pedido": datetime.now(timezone.utc),
        "estado": estado,
        "items": items,
        "total": float(total),
        "metodo_pago": metodo_pago,
        "direccion_envio": direccion_envio
    }

    try:
        # Registrar el pedido
        resultado = db.pedidos.insert_one(pedido)
        print(f"\n[ÉXITO] Pedido registrado correctamente con ID: {resultado.inserted_id}")
        print(f"Total del pedido: ${total:.2f}")

        # Descontar stock de los productos vendidos
        for item in items:
            db.productos.update_one(
                {"_id": item["producto_id"]},
                {"$inc": {"stock": -item["cantidad"]}}
            )
            print(f"  > Stock actualizado para producto ID {item['producto_id']}")

    except WriteError as we:
        print(f"\n[ERROR de Validación] MongoDB rechazó el pedido por violación de esquema.")
        print(f"Detalle: {we.details.get('errmsg', we)}")
    except PyMongoError as e:
        print(f"\n[ERROR] Ocurrió un error al registrar el pedido: {e}")

def listar_pedidos(db):
    print("\n--- Lista de Pedidos ---")
    try:
        pedidos = list(db.pedidos.find())
        if not pedidos:
            print("No hay pedidos registrados.")
            return []

        for ped in pedidos:
            print(f"\nID Pedido: {ped['_id']}")
            
            # Obtener nombre del cliente
            cliente = db.clientes.find_one({"_id": ped["cliente_id"]})
            nombre_cliente = cliente["nombre"] if cliente else f"Desconocido (ID: {ped['cliente_id']})"
            
            # Formatear fecha
            fecha = ped["fecha_pedido"]
            fecha_str = fecha.strftime("%Y-%m-%d %H:%M:%S UTC") if isinstance(fecha, datetime) else str(fecha)
            
            print(f"  Cliente: {nombre_cliente} | Fecha: {fecha_str} | Estado: {ped['estado'].upper()}")
            print(f"  Método de Pago: {ped['metodo_pago'].replace('_', ' ').capitalize()}")
            print(f"  Dirección de Envío: {ped['direccion_envio']['calle']}, {ped['direccion_envio']['ciudad']}, {ped['direccion_envio']['region']}")
            print("  Items:")
            for item in ped["items"]:
                prod = db.productos.find_one({"_id": item["producto_id"]})
                nombre_prod = prod["nombre"] if prod else f"Producto eliminado (ID: {item['producto_id']})"
                print(f"    - {nombre_prod} x{item['cantidad']} @ ${item['precio_unitario']:.2f} c/u")
            print(f"  TOTAL: ${ped['total']:.2f}")
        return pedidos
    except PyMongoError as e:
        print(f"[ERROR] Error al consultar pedidos: {e}")
        return []

def actualizar_pedido(db):
    print("\n--- Actualizar Pedido ---")
    id_str = input("Ingrese el ID del pedido a actualizar: ").strip()
    try:
        pedido_id = ObjectId(id_str)
    except Exception:
        print("[ERROR] El ID ingresado no tiene un formato válido de ObjectId.")
        return

    try:
        pedido = db.pedidos.find_one({"_id": pedido_id})
        if not pedido:
            print("[ERROR] Pedido no encontrado.")
            return

        print(f"\nPedido encontrado. Estado actual: {pedido['estado'].upper()}")
        print("¿Qué desea modificar?")
        print("1. Cambiar Estado")
        print("2. Modificar Dirección de Envío")
        print("3. Volver")
        opc = input("Opción: ").strip()

        if opc == "1":
            nuevo_estado = obtener_estado()
            db.pedidos.update_one({"_id": pedido_id}, {"$set": {"estado": nuevo_estado}})
            print(f"[ÉXITO] Estado del pedido actualizado a: {nuevo_estado.upper()}")
        elif opc == "2":
            dir_act = pedido["direccion_envio"]
            print("\n-- Modificar Dirección --")
            calle = input(f"Calle [{dir_act['calle']}]: ").strip() or dir_act['calle']
            ciudad = input(f"Ciudad [{dir_act['ciudad']}]: ").strip() or dir_act['ciudad']
            region = input(f"Región [{dir_act['region']}]: ").strip() or dir_act['region']
            cp = input(f"Código Postal [{dir_act['codigo_postal']}]: ").strip() or dir_act['codigo_postal']

            nueva_direccion = {
                "calle": calle,
                "ciudad": ciudad,
                "region": region,
                "codigo_postal": cp
            }
            db.pedidos.update_one({"_id": pedido_id}, {"$set": {"direccion_envio": nueva_direccion}})
            print("[ÉXITO] Dirección de envío actualizada.")
        else:
            print("Operación cancelada.")
    except WriteError as we:
        print(f"\n[ERROR de Validación] MongoDB rechazó los cambios por violación de esquema.")
        print(f"Detalle: {we.details.get('errmsg', we)}")
    except PyMongoError as e:
        print(f"[ERROR] No se pudo actualizar el pedido: {e}")

def eliminar_pedido(db):
    print("\n--- Eliminar Pedido ---")
    id_str = input("Ingrese el ID del pedido a eliminar: ").strip()
    try:
        pedido_id = ObjectId(id_str)
    except Exception:
        print("[ERROR] El ID ingresado no tiene un formato válido de ObjectId.")
        return

    try:
        pedido = db.pedidos.find_one({"_id": pedido_id})
        if not pedido:
            print("[ERROR] Pedido no encontrado.")
            return

        # Advertir al usuario y preguntar si desea devolver el stock
        print(f"[ADVERTENCIA] Se eliminará el pedido de la base de datos.")
        reponer_stock = input("¿Desea reponer en el inventario el stock de los productos de este pedido? (s/n): ").strip().lower()

        if reponer_stock == 's':
            for item in pedido["items"]:
                db.productos.update_one(
                    {"_id": item["producto_id"]},
                    {"$inc": {"stock": item["cantidad"]}}
                )
            print("  > Stock devuelto a los productos correspondientes.")

        resultado = db.pedidos.delete_one({"_id": pedido_id})
        if resultado.deleted_count > 0:
            print("[ÉXITO] Pedido eliminado correctamente.")
        else:
            print("[ERROR] No se pudo eliminar el pedido.")
    except PyMongoError as e:
        print(f"[ERROR] No se pudo eliminar el pedido: {e}")

def menu_pedidos(db):
    while True:
        print("\n=== MENÚ PEDIDOS ===")
        print("1. Crear Pedido")
        print("2. Listar Pedidos")
        print("3. Actualizar Pedido")
        print("4. Eliminar Pedido")
        print("5. Volver al Menú Principal")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            crear_pedido(db)
        elif opcion == "2":
            listar_pedidos(db)
        elif opcion == "3":
            actualizar_pedido(db)
        elif opcion == "4":
            eliminar_pedido(db)
        elif opcion == "5":
            break
        else:
            print("[ERROR] Opción no válida. Intente de nuevo.")
