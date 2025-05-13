from dataclasses import dataclass
from typing import List
from enum import Enum

class Category(Enum):
    DESECHABLES = "Desechables"
    DESINFECCION = "Desinfección"
    ELECTRODOS = "Electrodos"
    LIMPIEZA = "Limpieza"
    EQUIPAMIENTO = "Equipamiento"
    CONSUMIBLES = "Consumibles"

@dataclass
class Product:
    name: str
    category: Category
    price: float  # in Mexican pesos
    description: str
    stock: int

class ProductCatalog:
    def __init__(self):
        self.products: List[Product] = [
            # Disposables
            Product(
                "Guantes de Látex Talla M",
                Category.DESECHABLES,
                89.90,
                "Guantes de látex desechables, caja con 100 piezas",
                50
            ),
            Product(
                "Cubrebocas Quirúrgicos",
                Category.DESECHABLES,
                149.90,
                "Caja con 50 cubrebocas quirúrgicos de 3 capas",
                100
            ),
            
            # Desinfección
            Product(
                "Alcohol en Gel 500ml",
                Category.DESINFECCION,
                79.90,
                "Alcohol en gel con glicerina, 500ml",
                30
            ),
            Product(
                "Toallitas Desinfectantes",
                Category.DESINFECCION,
                129.90,
                "Paquete con 100 toallitas desinfectantes",
                40
            ),
            
            # Electrodos
            Product(
                "Electrodos ECG Adulto",
                Category.ELECTRODOS,
                299.90,
                "Set de 10 electrodos para ECG en adultos",
                25
            ),
            Product(
                "Electrodos Pediátricos",
                Category.ELECTRODOS,
                349.90,
                "Set de 10 electrodos para ECG pediátrico",
                20
            ),
            
            # Limpieza
            Product(
                "Jabón Líquido Antiséptico",
                Category.LIMPIEZA,
                89.90,
                "Jabón líquido antiséptico 500ml",
                35
            ),
            Product(
                "Detergente Enzimático",
                Category.LIMPIEZA,
                199.90,
                "Detergente enzimático para limpieza de equipos médicos",
                15
            ),
            
            # Equipamiento
            Product(
                "Estetoscopio Littmann",
                Category.EQUIPAMIENTO,
                2499.90,
                "Estetoscopio Littmann Classic III",
                10
            ),
            Product(
                "Tensiómetro Digital",
                Category.EQUIPAMIENTO,
                899.90,
                "Tensiómetro digital automático brazo",
                20
            ),
            
            # Consumibles
            Product(
                "Jeringas 5ml",
                Category.CONSUMIBLES,
                49.90,
                "Caja con 100 jeringas estériles de 5ml",
                200
            ),
            Product(
                "Agujas 21G",
                Category.CONSUMIBLES,
                39.90,
                "Caja con 100 agujas estériles 21G",
                150
            )
        ]
    
    def get_products_by_category(self, category: Category) -> List[Product]:
        return [p for p in self.products if p.category == category]
    
    def search_product(self, name: str) -> List[Product]:
        return [p for p in self.products if name.lower() in p.name.lower()]
    
    def get_all_products(self) -> List[Product]:
        return self.products
    
    def get_product_by_name(self, name: str) -> Product:
        return next((p for p in self.products if p.name.lower() == name.lower()), None)

def show_products(products: List[Product]):
    for p in products:
        print(f"\n{p.name}")
        print(f"Categoría: {p.category.value}")
        print(f"Precio: ${p.price:.2f} MXN")
        print(f"Descripción: {p.description}")
        print(f"Stock disponible: {p.stock}")