import sys
from database import get_db
from crud_clientes import menu_clientes
from crud_productos import menu_productos
from crud_pedidos import menu_pedidos

def main():
    print("Iniciando conexión con MongoDB...")
    db = get_db()
    print("[ÉXITO] Conexión establecida correctamente.")

    while True:
        print("\n==================================")
        print("   SISTEMA DE GESTIÓN DE VENTAS")
        print("==================================")
        print("1. Gestionar Clientes")
        print("2. Gestionar Productos")
        print("3. Gestionar Pedidos")
        print("4. Salir")
        print("==================================")
        opcion = input("Seleccione una opción: ").strip()

        if opcion == "1":
            menu_clientes(db)
        elif opcion == "2":
            menu_productos(db)
        elif opcion == "3":
            menu_pedidos(db)
        elif opcion == "4":
            print("\n¡Gracias por usar el sistema! Saliendo...")
            sys.exit(0)
        else:
            print("[ERROR] Opción no válida. Por favor, intente de nuevo.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nPrograma interrumpido por el usuario. Saliendo...")
        sys.exit(0)
