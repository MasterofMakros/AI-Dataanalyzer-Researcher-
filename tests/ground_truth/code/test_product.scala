// Scala Test File
package com.example

case class Product(id: Int, name: String, price: Double)

object ProductService {
  def calculateTotal(products: List[Product]): Double = 
    products.map(_.price).sum
  
  def main(args: Array[String]): Unit = {
    val products = List(
      Product(1, "Laptop", 999.99),
      Product(2, "Mouse", 29.99)
    )
    println(s"Total:  EUR")
  }
}
